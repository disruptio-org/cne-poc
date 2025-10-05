from __future__ import annotations

from typing import Iterable, List

from api.app.schemas import ValidationBadge


REQUIRED_COLUMNS = ["ORGAO", "NOME_LISTA", "TIPO", "SIGLA"]


def validate(records: Iterable[dict[str, str]]) -> List[List[ValidationBadge]]:
    results: List[List[ValidationBadge]] = []
    for record in records:
        badges: List[ValidationBadge] = []
        for column in REQUIRED_COLUMNS:
            value = record.get(column, "")
            if value:
                badges.append(ValidationBadge(field=column, status="ok", message=None))
            else:
                badges.append(ValidationBadge(field=column, status="warning", message="Valor ausente"))
        results.append(badges)
    return results
