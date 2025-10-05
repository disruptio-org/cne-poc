from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from .fuzzy import match_sigla

NORMALIZED_COLUMNS = [
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
]


def normalize(records: Iterable[dict[str, str]]) -> List[dict[str, str]]:
    normalized: List[dict[str, str]] = []
    counters: dict[str, int] = defaultdict(int)
    for record in records:
        data = {column: record.get(column, "").strip() for column in NORMALIZED_COLUMNS}
        tipo = data.get("tipo", "").upper()
        if tipo:
            counters[tipo] += 1
            data["num_ordem"] = str(counters[tipo])
        else:
            data["num_ordem"] = data.get("num_ordem", "")
        if data["sigla"]:
            data["sigla"], metadata = match_sigla(data["sigla"])
            if metadata:
                data["observacao"] = metadata.get("descricao", data["observacao"])
        normalized.append(data)
    return normalized
