from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
import re
from typing import Iterable, List

from api.app.schemas import ValidationBadge

from .fuzzy import FUZZY_CUTOFF, FUZZY_WARNING_THRESHOLD, match_sigla

REQUIRED_COLUMNS = ["orgao", "lista", "tipo", "sigla"]
FIELD_ORDER = ["orgao", "lista", "tipo", "sigla", "dtmnfr", "num_ordem"]
ALLOWED_TIPOS = {"TITULAR", "SUPLENTE", "GCE"}
ORGAO_PATTERN = re.compile(r"^[A-Za-zÀ-ÿ0-9 .,'ºª/&()\-]+$")
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")
SEVERITY = {"ok": 0, "aviso": 1, "erro": 2}


def _merge_messages(existing: str | None, new: str | None) -> str | None:
    if not existing:
        return new
    if not new or new in existing:
        return existing
    return f"{existing}; {new}"


def _update_badge(
    row_badges: dict[str, ValidationBadge],
    field: str,
    status: str,
    message: str | None,
) -> None:
    existing = row_badges.get(field)
    if existing:
        if SEVERITY[status] < SEVERITY[existing.status]:
            return
        if SEVERITY[status] == SEVERITY[existing.status]:
            message = _merge_messages(existing.message, message)
    row_badges[field] = ValidationBadge(field=field, status=status, message=message)


def _valid_date(value: str) -> bool:
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def validate(records: Iterable[dict[str, str]]) -> List[List[ValidationBadge]]:
    rows = list(records)
    badge_maps: List[dict[str, ValidationBadge]] = []
    order_by_list: dict[str, list[tuple[int, int]]] = defaultdict(list)
    first_index_by_list: dict[str, int] = {}
    suplente_lists: set[str] = set()
    titular_lists: set[str] = set()

    for index, record in enumerate(rows):
        row_badges: dict[str, ValidationBadge] = {}
        badge_maps.append(row_badges)

        for column in REQUIRED_COLUMNS:
            value = (record.get(column, "") or "").strip()
            if column == "sigla":
                if value:
                    _update_badge(row_badges, column, "ok", None)
                else:
                    _update_badge(row_badges, column, "aviso", "Sigla ausente")
            else:
                status = "ok" if value else "erro"
                message = None if status == "ok" else "Valor obrigatório ausente"
                _update_badge(row_badges, column, status, message)

        dtmnfr_value = record.get("dtmnfr")
        if dtmnfr_value is not None:
            cleaned = dtmnfr_value.strip()
            if cleaned:
                _update_badge(row_badges, "dtmnfr", "ok", None)
            else:
                _update_badge(row_badges, "dtmnfr", "aviso", "Data de nomeação ausente")

        num_value = (record.get("num_ordem", "") or "").strip()
        if num_value:
            try:
                number = int(num_value)
            except ValueError:
                _update_badge(row_badges, "num_ordem", "erro", "Número de ordem inválido")
            else:
                _update_badge(row_badges, "num_ordem", "ok", None)
                lista_key = (record.get("lista", "") or "").strip().lower()
                if lista_key:
                    order_by_list[lista_key].append((index, number))
        elif "num_ordem" in record:
            _update_badge(row_badges, "num_ordem", "erro", "Número de ordem ausente")

        lista_value = (record.get("lista", "") or "").strip()
        if lista_value:
            list_key = lista_value.lower()
            first_index_by_list.setdefault(list_key, index)
            tipo_value = (record.get("tipo", "") or "").strip().upper()
            if tipo_value == "SUPLENTE":
                suplente_lists.add(list_key)
            if tipo_value == "TITULAR":
                titular_lists.add(list_key)

    for index, record in enumerate(rows):
        orgao_value = (record.get("orgao", "") or "").strip()
        if orgao_value and not ORGAO_PATTERN.fullmatch(orgao_value):
            _update_badge(
                badge_maps[index],
                "orgao",
                "aviso",
                "Formato de órgão inesperado",
            )

        tipo_value = (record.get("tipo", "") or "").strip()
        if tipo_value:
            normalized_tipo = tipo_value.upper()
            if normalized_tipo not in ALLOWED_TIPOS:
                _update_badge(badge_maps[index], "tipo", "erro", "Tipo inválido")
        dtmnfr_value = (record.get("dtmnfr", "") or "").strip()
        if dtmnfr_value:
            if not _valid_date(dtmnfr_value):
                _update_badge(
                    badge_maps[index],
                    "dtmnfr",
                    "erro",
                    "Formato de data inválido (use AAAA-MM-DD ou DD/MM/AAAA)",
                )
        elif record.get("dtmnfr") is not None:
            _update_badge(badge_maps[index], "dtmnfr", "aviso", "Data de nomeação ausente")

        raw_sigla = (record.get("_sigla_original") or record.get("sigla") or "").strip()
        if raw_sigla:
            matched_sigla, metadata = match_sigla(raw_sigla)
            if metadata is None:
                _update_badge(
                    badge_maps[index],
                    "sigla",
                    "erro",
                    "Sigla não encontrada no cadastro mestre",
                )
            else:
                ratio = SequenceMatcher(None, raw_sigla.upper(), matched_sigla).ratio()
                if ratio < FUZZY_CUTOFF:
                    _update_badge(
                        badge_maps[index],
                        "sigla",
                        "erro",
                        "Diferença grande entre sigla informada e cadastro mestre",
                    )
                elif ratio < FUZZY_WARNING_THRESHOLD:
                    _update_badge(
                        badge_maps[index],
                        "sigla",
                        "aviso",
                        "Sigla ajustada para cadastro mestre",
                    )

    for list_key, entries in order_by_list.items():
        entries.sort(key=lambda item: (item[1], item[0]))
        expected = 1
        for row_index, number in entries:
            if number != expected:
                lista_nome = rows[row_index].get("lista", "")
                _update_badge(
                    badge_maps[row_index],
                    "num_ordem",
                    "aviso",
                    f"Número de ordem esperado {expected} para a lista '{lista_nome}'",
                )
            expected = number + 1

    for list_key in titular_lists:
        if list_key and list_key not in suplente_lists:
            row_index = first_index_by_list.get(list_key)
            if row_index is not None:
                _update_badge(
                    badge_maps[row_index],
                    "lista",
                    "aviso",
                    "Lista sem suplentes cadastrados",
                )

    results: List[List[ValidationBadge]] = []
    for row_badges in badge_maps:
        ordered = [row_badges[field] for field in FIELD_ORDER if field in row_badges]
        for field, badge in row_badges.items():
            if field not in FIELD_ORDER:
                ordered.append(badge)
        results.append(ordered)
    return results
