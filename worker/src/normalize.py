from __future__ import annotations

from typing import Iterable, List

from .fuzzy import match_sigla

NORMALIZED_COLUMNS = [
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


def normalize(records: Iterable[dict[str, str]]) -> List[dict[str, str]]:
    normalized: List[dict[str, str]] = []
    for record in records:
        data = {column: record.get(column, "").strip() for column in NORMALIZED_COLUMNS}
        if data["sigla"]:
            data["sigla"], metadata = match_sigla(data["sigla"])
            if metadata:
                data["observacao"] = metadata.get("descricao", data["observacao"])
        normalized.append(data)
    return normalized
