from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, List, Tuple

from .extract import EXPECTED_COLUMNS
from .fuzzy import match_sigla

NORMALIZED_COLUMNS = EXPECTED_COLUMNS


def _normalize_tipo(value: str) -> str:
    normalized = value.strip().upper()
    if not normalized:
        return ""
    if normalized.startswith("TITULAR"):
        return "2"
    if normalized.startswith("SUPLENTE"):
        return "3"
    if normalized in {"2", "3"}:
        return normalized
    return "3"


def _split_lista(raw_value: str) -> Tuple[str, str]:
    value = raw_value.strip()
    if not value:
        return "", ""

    lower_value = value.lower()
    working = value
    removed_prefix = False
    if lower_value.startswith("coligacao "):
        working = value[len("Coligacao ") :].strip()
        removed_prefix = True

    if " - " in working:
        name, symbol = working.rsplit(" - ", 1)
        return name.strip(), symbol.strip()

    if "(" in working and ")" in working:
        name, remainder = working.split("(", 1)
        symbol = remainder.split(")", 1)[0]
        return name.strip(), symbol.strip()

    if "§" in value:
        left, right = value.split("§", 1)
        symbol_tokens = left.strip().split()
        symbol = symbol_tokens[-1] if symbol_tokens else ""
        name = right.strip() or working
        return name, symbol

    if removed_prefix:
        acronym = "".join(token[0] for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", working))
        return working, acronym.upper()

    return value, ""


def _is_independent(raw_lista: str) -> str:
    lowered = raw_lista.lower()
    if not lowered:
        return ""
    if "coligacao" in lowered:
        return "N"
    if "lista unica" in lowered:
        return "S"
    return "N"


def normalize(records: Iterable[dict[str, str]]) -> List[dict[str, str]]:
    normalized: List[dict[str, str]] = []
    counters: dict[str, int] = defaultdict(int)
    for record in records:
        data = {column: record.get(column, "").strip() for column in NORMALIZED_COLUMNS}

        raw_lista = record.get("_raw_lista", data.get("NOME_LISTA", ""))
        nome_lista, simbolo = _split_lista(raw_lista)
        data["NOME_LISTA"] = nome_lista
        data["SIMBOLO"] = simbolo

        data["INDEPENDENTE"] = _is_independent(raw_lista)

        tipo_code = _normalize_tipo(record.get("TIPO", ""))
        data["TIPO"] = tipo_code
        if tipo_code:
            counters[tipo_code] += 1
            data["NUM_ORDEM"] = str(counters[tipo_code])
        else:
            data["NUM_ORDEM"] = data.get("NUM_ORDEM", "")

        sigla_raw = record.get("_raw_sigla", data.get("SIGLA", ""))
        if sigla_raw:
            matched_sigla, metadata = match_sigla(sigla_raw)
            data["SIGLA"] = matched_sigla
            if metadata:
                data["PARTIDO_PROPONENTE"] = metadata.get(
                    "descricao", data.get("PARTIDO_PROPONENTE", "")
                )
            elif not data.get("PARTIDO_PROPONENTE"):
                data["PARTIDO_PROPONENTE"] = sigla_raw.upper()
        else:
            data["SIGLA"] = ""

        data["NOME_CANDIDATO"] = " ".join(data["NOME_CANDIDATO"].split())

        normalized.append(data)
    return normalized
