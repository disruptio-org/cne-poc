from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .extract import EXPECTED_COLUMNS


def write_csv(job_id: str, records: Iterable[dict[str, str]], base_dir: Path) -> Path:
    job_dir = base_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    csv_path = job_dir / "output.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_COLUMNS, delimiter=";")
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in EXPECTED_COLUMNS})
    return csv_path
