from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, List, Tuple
from .fuzzy import match_sigla


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
    counters: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for record in records:
        dtmnfr = (record.get("DTMNFR", "") or "").strip()
        orgao = (record.get("ORGAO", "") or "").strip()
        raw_tipo = record.get("TIPO", "") or ""
        tipo = _normalize_tipo(raw_tipo)

        raw_lista = record.get("_raw_lista") or record.get("NOME_LISTA", "")
        raw_lista = raw_lista.strip()
        nome_lista_hint = (record.get("NOME_LISTA", "") or "").strip()
        nome_lista_from_raw, simbolo = _split_lista(raw_lista or nome_lista_hint)
        nome_lista = nome_lista_hint or nome_lista_from_raw

        independente = _is_independent(raw_lista or nome_lista)

        sigla_value = (record.get("SIGLA", "") or "").strip()
        sigla_raw = (record.get("_raw_sigla") or sigla_value).strip()
        partido = (record.get("PARTIDO_PROPONENTE", "") or "").strip()
        sigla = ""
        metadata: dict | None = None
        if sigla_raw:
            sigla, metadata = match_sigla(sigla_raw)
        elif sigla_value:
            sigla, metadata = match_sigla(sigla_value)
        if metadata:
            partido = metadata.get("descricao", partido)
        elif not partido and sigla_raw:
            partido = sigla_raw.upper()
        if not sigla:
            sigla = sigla_raw.upper() if sigla_raw else sigla_value.upper()

        nome_candidato = " ".join((record.get("NOME_CANDIDATO", "") or "").split())

        counter_key = (dtmnfr, orgao.upper(), sigla.upper(), nome_lista.upper(), tipo)
        num_ordem = ""
        if tipo:
            counters[counter_key] += 1
            num_ordem = str(counters[counter_key])

        normalized.append(
            {
                "DTMNFR": dtmnfr,
                "ORGAO": orgao,
                "TIPO": tipo,
                "SIGLA": sigla,
                "SIMBOLO": simbolo,
                "NOME_LISTA": nome_lista,
                "NUM_ORDEM": num_ordem,
                "NOME_CANDIDATO": nome_candidato,
                "PARTIDO_PROPONENTE": partido,
                "INDEPENDENTE": independente,
            }
        )
    return normalized
