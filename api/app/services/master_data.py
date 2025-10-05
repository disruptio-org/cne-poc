from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from ..schemas import MasterDataResponse, MasterRecord

LOGGER = logging.getLogger(__name__)

DATA_DIR = Path("data/master")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class MasterDataService:
    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory or DATA_DIR

    def _load_files(self) -> Iterable[Path]:
        return sorted(self._directory.glob("*.json"))

    def list_records(self) -> MasterDataResponse:
        records: list[MasterRecord] = []
        for file in self._load_files():
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        records.append(MasterRecord(**item))
                elif isinstance(data, dict):
                    records.append(MasterRecord(**data))
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.exception("Failed to load master data from %s", file)
                raise exc
        return MasterDataResponse(records=records)

    def upsert(self, record: MasterRecord) -> None:
        file = self._directory / f"{record.sigla.lower()}.json"
        file.write_text(record.json(indent=2, ensure_ascii=False), encoding="utf-8")

    def bulk_load(self, records: Iterable[MasterRecord]) -> None:
        for record in records:
            self.upsert(record)
