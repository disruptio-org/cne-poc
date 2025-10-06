from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from ml.registry import ModelRegistry

JOBS_FILE = Path("data/state/jobs.json")
PROCESSED_DIR = Path("data/processed")


def _approved_jobs() -> List[str]:
    if not JOBS_FILE.exists():
        return []
    data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    return [job_id for job_id, record in data.items() if record.get("status") == "approved"]


def _load_rows(job_id: str) -> List[dict[str, str]]:
    csv_path = PROCESSED_DIR / job_id / "output.csv"
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        return list(reader)


def build_training_corpus() -> List[dict[str, str]]:
    rows: List[dict[str, str]] = []
    for job_id in _approved_jobs():
        rows.extend(_load_rows(job_id))
    return rows


def train(model_name: str = "baseline") -> None:
    registry = ModelRegistry()
    rows = build_training_corpus()
    metrics = {
        "rows": len(rows),
        "unique_siglas": len({row.get("SIGLA") for row in rows if row.get("SIGLA")}),
    }
    registry.register(model_name=model_name, metrics=metrics)


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    train()
