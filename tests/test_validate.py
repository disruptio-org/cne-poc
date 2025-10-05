from __future__ import annotations

from typing import Iterable

from api.app.schemas import ValidationBadge

from worker.src import validate


def _badge_lookup(badges: Iterable[ValidationBadge]) -> dict[str, ValidationBadge]:
    return {badge.field: badge for badge in badges}


def test_validate_accepts_valid_records() -> None:
    records = [
        {
            "orgao": "Conselho Nacional de Educação",
            "lista": "Lista Única",
            "tipo": "Titular",
            "num_ordem": "1",
            "sigla": "MEC",
            "_sigla_original": "Mec",
            "dtmnfr": "2024-01-15",
        },
        {
            "orgao": "Conselho Nacional de Educação",
            "lista": "Lista Única",
            "tipo": "Suplente",
            "num_ordem": "2",
            "sigla": "INEP",
            "_sigla_original": "Inep",
            "dtmnfr": "15/02/2024",
        },
    ]

    results = validate.validate(records)
    assert len(results) == 2
    first = _badge_lookup(results[0])
    second = _badge_lookup(results[1])

    assert first["orgao"].status == "ok"
    assert first["lista"].status == "ok"
    assert first["tipo"].status == "ok"
    assert first["sigla"].status == "ok"
    assert first["dtmnfr"].status == "ok"
    assert first["num_ordem"].status == "ok"

    assert second["sigla"].status == "ok"
    assert second["dtmnfr"].status == "ok"
    assert second["num_ordem"].status == "ok"


def test_validate_emits_warnings_for_thresholds() -> None:
    records = [
        {
            "orgao": "Conselho Nacional de Educação",
            "lista": "Lista Observada",
            "tipo": "Titular",
            "num_ordem": "1",
            "sigla": "MEC",
            "_sigla_original": "Mecx",
            "dtmnfr": "2024-01-01",
        },
        {
            "orgao": "Conselho Nacional de Educação",
            "lista": "Lista Observada",
            "tipo": "Titular",
            "num_ordem": "3",
            "sigla": "MEC",
            "_sigla_original": "Mec",
            "dtmnfr": "2024-01-02",
        },
    ]

    results = validate.validate(records)
    first = _badge_lookup(results[0])
    second = _badge_lookup(results[1])

    assert first["sigla"].status == "aviso"
    assert first["sigla"].message
    assert second["num_ordem"].status == "aviso"
    assert second["num_ordem"].message
    assert first["lista"].status == "aviso"


def test_validate_blocks_errors() -> None:
    records = [
        {
            "orgao": "",
            "lista": "Lista Sem Suplente",
            "tipo": "Outro",
            "num_ordem": "abc",
            "sigla": "XYZ",
            "_sigla_original": "XYZ",
            "dtmnfr": "2024/14/01",
        }
    ]

    results = validate.validate(records)
    row = _badge_lookup(results[0])

    assert row["orgao"].status == "erro"
    assert row["tipo"].status == "erro"
    assert row["sigla"].status == "erro"
    assert row["dtmnfr"].status == "erro"
    assert row["num_ordem"].status == "erro"
