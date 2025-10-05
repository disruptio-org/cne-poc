from __future__ import annotations

from typing import Dict, List

EXPECTED_COLUMNS = [
    "orgao",
    "lista",
    "tipo",
    "linha",
    "descricao",
    "valor",
    "sigla",
    "fonte",
    "competencia",
    "observacao",
]


def extract_records(segments: Dict[str, List[dict]]) -> List[dict[str, str]]:
    records: List[dict[str, str]] = []
    current: dict[str, str] = {column: "" for column in EXPECTED_COLUMNS}
    line_number = 1
    for key, entries in segments.items():
        for entry in entries:
            text = entry["content"].strip()
            if ":" in text:
                prefix, value = [part.strip() for part in text.split(":", 1)]
                lowered = prefix.lower()
                if lowered in current:
                    current[lowered] = value
            elif text:
                current["descricao"] = text
            current["linha"] = str(line_number)
            line_number += 1
            if all(current.get(col) for col in ("orgao", "lista", "tipo")):
                records.append(current.copy())
                current = {column: "" for column in EXPECTED_COLUMNS}
    if any(current.values()):
        records.append(current)
    return records
