from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from api.app.schemas import ModelHistoryResponse, ModelMetadata

REGISTRY_FILE = Path("data/state/model_registry.json")
REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_history() -> List[dict]:
    if not REGISTRY_FILE.exists():
        return []
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _save_history(history: Iterable[dict]) -> None:
    REGISTRY_FILE.write_text(json.dumps(list(history), indent=2), encoding="utf-8")


@dataclass
class ModelRecord:
    model_name: str
    version: str
    created_at: str
    status: str
    metrics: dict


class ModelRegistry:
    def __init__(self) -> None:
        self._history = _load_history()

    def register(self, model_name: str, metrics: dict, status: str = "candidate") -> ModelRecord:
        version = f"{len(self._history) + 1:03d}"
        record = ModelRecord(
            model_name=model_name,
            version=version,
            created_at=datetime.utcnow().isoformat(),
            status=status,
            metrics=metrics,
        )
        self._history.append(asdict(record))
        _save_history(self._history)
        return record

    def promote(self, version: str) -> None:
        for record in self._history:
            record["status"] = "archived" if record["version"] != version else "production"
        _save_history(self._history)

    def rollback(self, version: str) -> None:
        for record in self._history:
            if record["version"] == version:
                record["status"] = "production"
            elif record["status"] == "production":
                record["status"] = "archived"
        _save_history(self._history)

    def update_metrics(self, version: str, metrics: dict) -> None:
        for record in self._history:
            if record["version"] == version:
                record.setdefault("metrics", {}).update(metrics)
        _save_history(self._history)

    def history(self) -> ModelHistoryResponse:
        items = [ModelMetadata(**record) for record in self._history]
        return ModelHistoryResponse(items=items)
