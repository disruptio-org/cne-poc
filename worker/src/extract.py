from __future__ import annotations

import unicodedata
from typing import Dict, Iterator, List

EXPECTED_COLUMNS = [
    "DTMNFR",
    "ORGAO",
    "TIPO",
    "SIGLA",
    "SIMBOLO",
    "NOME_LISTA",
    "NUM_ORDEM",
    "NOME_CANDIDATO",
    "PARTIDO_PROPONENTE",
    "INDEPENDENTE",
]

FIELD_MAPPING = {
    "dtmnfr": "DTMNFR",
    "competencia": "DTMNFR",
    "orgao": "ORGAO",
    "lista": "NOME_LISTA",
    "tipo": "TIPO",
    "sigla": "SIGLA",
    "descricao": "NOME_CANDIDATO",
    "partido_proponente": "PARTIDO_PROPONENTE",
}

METADATA_MAPPING = {
    "dtmnfr": "DTMNFR",
}


def _init_record() -> dict[str, str]:
    record = {column: "" for column in EXPECTED_COLUMNS}
    record["_raw_lista"] = ""
    record["_raw_sigla"] = ""
    return record

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


def _iter_entries(segments: Dict[str, List[dict]]) -> Iterator[dict[str, str]]:
    for entry in sorted(
        (item for items in segments.values() for item in items),
        key=lambda data: data.get("index", 0),
    ):
        yield entry


def extract_records(segments: Dict[str, List[dict]]) -> List[dict[str, str]]:
    records: List[dict[str, str]] = []
    metadata = _extract_metadata(segments)
    current = _init_record()

    def finalize_record() -> None:
        nonlocal current
        if any(current.get(column) for column in ("ORGAO", "NOME_LISTA", "TIPO", "NOME_CANDIDATO")):
            record = current.copy()
            for meta_key, column in METADATA_MAPPING.items():
                if not record.get(column):
                    record[column] = metadata.get(meta_key, "")
            records.append(record)
        current = _init_record()

    for entry in _iter_entries(segments):
        text = entry["content"].strip()
        if not text:
            if any(current.get(column) for column in ("ORGAO", "NOME_LISTA", "TIPO", "NOME_CANDIDATO")):
                finalize_record()
            continue

        if ":" in text:
            prefix, value = [part.strip() for part in text.split(":", 1)]
            key = _normalize_key(prefix)
            column = FIELD_MAPPING.get(key)
            if column is None:
                continue
            if column == "ORGAO" and current["ORGAO"]:
                finalize_record()
            if column == "NOME_LISTA":
                current["_raw_lista"] = value
            if column == "SIGLA":
                current["_raw_sigla"] = value
            if column == "NOME_CANDIDATO":
                current[column] = " ".join(part for part in (current[column], value) if part).strip()
            else:
                current[column] = value
        else:
            if any(current.get(column) for column in ("ORGAO", "NOME_LISTA", "TIPO", "NOME_CANDIDATO")):
                current["NOME_CANDIDATO"] = " ".join(
                    part for part in (current["NOME_CANDIDATO"], text) if part
                ).strip()

    finalize_record()
    return records
