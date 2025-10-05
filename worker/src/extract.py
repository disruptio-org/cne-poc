from __future__ import annotations

import unicodedata
from typing import Dict, Iterable, List

EXPECTED_COLUMNS = [
    "orgao",
    "lista",
    "tipo",
    "num_ordem",
    "linha",
    "descricao",
    "valor",
    "sigla",
    "fonte",
    "competencia",
    "observacao",
    "dtmnfr",
]

def _normalize_key(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label)
    stripped = "".join(character for character in normalized if not unicodedata.combining(character))
    return stripped.lower().replace("-", "_").replace(" ", "_")


def _extract_metadata(segments: Dict[str, List[dict]]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for entry in _iter_entries(segments):
        text = entry["content"].strip()
        if not text:
            continue
        if text.lower().startswith("orgao"):
            break
        if ":" not in text:
            continue
        prefix, value = [part.strip() for part in text.split(":", 1)]
        key = _normalize_key(prefix)
        metadata[key] = value
    return metadata


def _iter_entries(segments: Dict[str, List[dict]]) -> Iterable[dict[str, str]]:
    for entry in sorted(
        (item for items in segments.values() for item in items),
        key=lambda data: data.get("index", 0),
    ):
        yield entry


def extract_records(segments: Dict[str, List[dict]]) -> List[dict[str, str]]:
    records: List[dict[str, str]] = []
    current: dict[str, str] = {column: "" for column in EXPECTED_COLUMNS}
    line_number = 1
    metadata = _extract_metadata(segments)

    def finalize_record() -> None:
        nonlocal current
        if any(value for key, value in current.items() if key not in {"num_ordem"}):
            record = current.copy()
            for key, value in metadata.items():
                if not record.get(key):
                    record[key] = value
            records.append(record)
        current = {column: "" for column in EXPECTED_COLUMNS}

    for entry in _iter_entries(segments):
        text = entry["content"].strip()
        if not text:
            if any(current.get(column) for column in ("orgao", "lista", "tipo", "descricao")):
                finalize_record()
            continue

        if ":" in text:
            prefix, value = [part.strip() for part in text.split(":", 1)]
            key = _normalize_key(prefix)
            if key not in current:
                current["observacao"] = " ".join(part for part in (current["observacao"], text) if part).strip()
            else:
                if key == "orgao" and current["orgao"]:
                    finalize_record()
                current[key] = value
        else:
            current["descricao"] = " ".join(part for part in (current["descricao"], text) if part).strip()

        current["linha"] = str(line_number)
        line_number += 1

    finalize_record()
    return [record for record in records if any(record.values())]
