from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from api.app.schemas import ValidationBadge

from .fuzzy import match_sigla


STATUS_PRIORITY = {"OK": 0, "AVISO": 1, "ERRO": 2}
ALLOWED_ORGAOS = {"AM", "CM", "AF"}
ALLOWED_TIPOS = {"2", "3"}
REQUIRED_COLUMNS = ["ORGAO", "NOME_LISTA", "TIPO", "SIGLA"]


def _update_badge(
    field_badges: dict[str, ValidationBadge], field: str, status: str, message: str | None
) -> None:
    badge = field_badges.get(field)
    if badge is None or STATUS_PRIORITY[status] > STATUS_PRIORITY[badge.status]:
        field_badges[field] = ValidationBadge(field=field, status=status, message=message)
        return
    if STATUS_PRIORITY[status] == STATUS_PRIORITY[badge.status] and message:
        if badge.message:
            if message not in badge.message:
                combined = f"{badge.message}; {message}"
                field_badges[field] = ValidationBadge(field=field, status=badge.status, message=combined)
        else:
            field_badges[field] = ValidationBadge(field=field, status=badge.status, message=message)


def _validate_required_fields(field_badges: dict[str, ValidationBadge], record: dict[str, str]) -> None:
    for column in REQUIRED_COLUMNS:
        value = (record.get(column, "") or "").strip()
        if value:
            _update_badge(field_badges, column, "OK", None)
        else:
            _update_badge(field_badges, column, "AVISO", "Valor ausente")


def _validate_dtmnfr(field_badges: dict[str, ValidationBadge], value: str) -> None:
    if not value:
        _update_badge(field_badges, "DTMNFR", "ERRO", "Data obrigatória ausente")
        return
    try:
        from datetime import datetime

        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        _update_badge(field_badges, "DTMNFR", "ERRO", "Data em formato inválido (YYYY-MM-DD)")
    else:
        _update_badge(field_badges, "DTMNFR", "OK", None)


def _validate_orgao(field_badges: dict[str, ValidationBadge], value: str) -> None:
    if not value:
        _update_badge(field_badges, "ORGAO", "ERRO", "Órgão obrigatório ausente")
        return
    normalized = value.upper()
    if normalized not in ALLOWED_ORGAOS:
        _update_badge(field_badges, "ORGAO", "ERRO", f"Órgão inválido: {value}")
    else:
        _update_badge(field_badges, "ORGAO", "OK", None)


def _validate_tipo(field_badges: dict[str, ValidationBadge], value: str) -> None:
    if not value:
        _update_badge(field_badges, "TIPO", "ERRO", "Tipo obrigatório ausente")
        return
    normalized = value.upper()
    if normalized not in ALLOWED_TIPOS:
        _update_badge(field_badges, "TIPO", "ERRO", f"Tipo inválido: {value}")
    else:
        _update_badge(field_badges, "TIPO", "OK", None)


def _evaluate_sigla_distance(
    field_badges: dict[str, ValidationBadge],
    raw_sigla: str,
    normalized_sigla: str,
) -> None:
    if not raw_sigla and not normalized_sigla:
        _update_badge(field_badges, "SIGLA", "AVISO", "Sigla ausente")
        return
    if not raw_sigla and normalized_sigla:
        # Already covered by required-field warning, keep informational badge
        _update_badge(field_badges, "SIGLA", "AVISO", "Sigla inferida")
        return
    candidate, metadata = match_sigla(raw_sigla)
    from difflib import SequenceMatcher

    ratio = SequenceMatcher(None, raw_sigla.upper(), candidate.upper()).ratio() if candidate else 0.0
    if metadata is None:
        _update_badge(field_badges, "SIGLA", "AVISO", "Sigla não encontrada no cadastro mestre")
    elif ratio < 0.95:
        message = f"Sigla ajustada para {candidate} (similaridade {ratio:.2f})"
        _update_badge(field_badges, "SIGLA", "AVISO", message)
    else:
        _update_badge(field_badges, "SIGLA", "OK", None)


def validate(
    records: Iterable[dict[str, str]], context: Mapping[str, Any] | None = None
) -> List[List[ValidationBadge]]:
    raw_records: list[dict[str, Any]] | None = None
    if context is not None:
        raw_records = list(context.get("raw_records", []) or [])

    results: List[dict[str, ValidationBadge]] = []
    order_groups: dict[tuple[str, str, str, str, str], list[tuple[int, str]]] = {}
    group_rows: dict[tuple[str, str, str, str], list[int]] = {}
    group_tipos: dict[tuple[str, str, str, str], set[str]] = {}

    for index, record in enumerate(records):
        field_badges: dict[str, ValidationBadge] = {}
        dtmnfr = (record.get("DTMNFR", "") or "").strip()
        orgao = (record.get("ORGAO", "") or "").strip()
        tipo = (record.get("TIPO", "") or "").strip()
        nome_lista = (record.get("NOME_LISTA", "") or "").strip()
        sigla = (record.get("SIGLA", "") or "").strip()

        _validate_required_fields(field_badges, record)
        _validate_dtmnfr(field_badges, dtmnfr)
        _validate_orgao(field_badges, orgao)
        _validate_tipo(field_badges, tipo)

        raw_sigla = ""
        if raw_records and index < len(raw_records):
            raw_record = raw_records[index]
            raw_sigla = (raw_record.get("_raw_sigla") or raw_record.get("SIGLA") or "").strip()
        _evaluate_sigla_distance(field_badges, raw_sigla, sigla)

        field_badges.setdefault("NOME_LISTA", ValidationBadge(field="NOME_LISTA", status="OK", message=None))
        if not nome_lista:
            _update_badge(field_badges, "NOME_LISTA", "AVISO", "Nome da lista ausente")

        order_key = (dtmnfr, orgao.upper(), sigla.upper(), nome_lista.upper(), tipo)
        order_groups.setdefault(order_key, []).append((index, record.get("NUM_ORDEM", "")))

        group_key = (dtmnfr, orgao.upper(), sigla.upper(), nome_lista.upper())
        group_rows.setdefault(group_key, []).append(index)
        group_tipos.setdefault(group_key, set()).add(tipo)

        results.append(field_badges)

    for entries in order_groups.values():
        parsed_entries: list[tuple[int, int, str]] = []
        for index, num_ordem in entries:
            raw_value = (num_ordem or "").strip()
            if not raw_value:
                _update_badge(results[index], "NUM_ORDEM", "ERRO", "NUM_ORDEM ausente para grupo")
                continue
            try:
                parsed_entries.append((index, int(raw_value), raw_value))
            except ValueError:
                _update_badge(results[index], "NUM_ORDEM", "ERRO", f"NUM_ORDEM inválido: {raw_value}")
        parsed_entries.sort(key=lambda item: item[1])
        expected = 1
        for index, value, raw_value in parsed_entries:
            if value != expected:
                if value < expected:
                    message = f"NUM_ORDEM repetido ou fora de ordem: {raw_value}"
                else:
                    message = f"NUM_ORDEM fora da sequência, esperado {expected}"
                _update_badge(results[index], "NUM_ORDEM", "ERRO", message)
                expected = value + 1
            else:
                _update_badge(results[index], "NUM_ORDEM", "OK", None)
                expected += 1

    for group_key, tipos in group_tipos.items():
        if "2" in tipos and "3" not in tipos:
            for index in group_rows.get(group_key, []):
                _update_badge(results[index], "TIPO", "AVISO", "Grupo sem suplentes (TIPO 3)")

    return [list(field_badges.values()) for field_badges in results]
