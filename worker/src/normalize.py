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
    "dtmnfr",
    "nome_lista",
]


def normalize(records: Iterable[dict[str, str]]) -> List[dict[str, str]]:
    normalized: List[dict[str, str]] = []
    counters: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for record in records:
        data = {column: record.get(column, "").strip() for column in NORMALIZED_COLUMNS}
        nome_lista = data.get("nome_lista") or data.get("lista", "")
        data["nome_lista"] = nome_lista
        tipo = data.get("tipo", "").upper()
        data["tipo"] = tipo
        if data["sigla"]:
            data["sigla"], metadata = match_sigla(data["sigla"])
            if metadata:
                data["observacao"] = metadata.get("descricao", data["observacao"])
        counter_key = (
            data.get("dtmnfr", ""),
            data.get("orgao", "").upper(),
            data.get("sigla", "").upper(),
            nome_lista.upper(),
            tipo,
        )
        if tipo:
            counters[counter_key] += 1
            data["num_ordem"] = str(counters[counter_key])
        else:
            data["num_ordem"] = data.get("num_ordem", "")
        normalized.append(data)
    return normalized
