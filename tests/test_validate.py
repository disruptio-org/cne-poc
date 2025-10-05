from __future__ import annotations

from worker.src import validate


def _badge_map(badges):
    return {badge.field: badge for badge in badges}


def test_validate_accepts_allowed_values():
    records = [
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "1",
        },
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "3",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "2",
        },
    ]

    results = validate.validate(records, context={"raw_records": records})
    titular = _badge_map(results[0])
    suplente = _badge_map(results[1])

    assert titular["DTMNFR"].status == "OK"
    assert titular["ORGAO"].status == "OK"
    assert titular["TIPO"].status == "OK"
    assert titular["SIGLA"].status == "OK"
    assert suplente["TIPO"].status == "OK"


def test_validate_flags_invalid_values():
    records = [
        {
            "DTMNFR": "20240101",
            "ORGAO": "XX",
            "TIPO": "1",
            "SIGLA": "",
            "NOME_LISTA": "",
            "NUM_ORDEM": "1",
        }
    ]

    results = validate.validate(records)
    badges = _badge_map(results[0])

    assert badges["DTMNFR"].status == "ERRO"
    assert badges["ORGAO"].status == "ERRO"
    assert badges["TIPO"].status == "ERRO"
    assert badges["SIGLA"].status == "AVISO"


def test_validate_detects_num_ordem_gap():
    records = [
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "1",
        },
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "3",
        },
    ]

    results = validate.validate(records)
    badges_first = _badge_map(results[0])
    badges_second = _badge_map(results[1])

    assert badges_first["NUM_ORDEM"].status == "OK"
    assert badges_second["NUM_ORDEM"].status == "ERRO"
    assert "sequência" in (badges_second["NUM_ORDEM"].message or "")


def test_validate_warns_missing_suplentes():
    records = [
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "1",
        },
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "2",
        },
    ]

    results = validate.validate(records)
    for badges in results:
        tipo_badge = _badge_map(badges)["TIPO"]
        assert tipo_badge.status == "AVISO"
        assert "suplentes" in (tipo_badge.message or "")


def test_validate_warns_fuzzy_sigla():
    records = [
        {
            "DTMNFR": "2024-01-01",
            "ORGAO": "AM",
            "TIPO": "2",
            "SIGLA": "MEC",
            "NOME_LISTA": "Lista Única",
            "NUM_ORDEM": "1",
        }
    ]
    raw_records = [{"SIGLA": "MECQ"}]

    results = validate.validate(records, context={"raw_records": raw_records})
    sigla_badge = _badge_map(results[0])["SIGLA"]

    assert sigla_badge.status == "AVISO"
    assert "ajustada" in (sigla_badge.message or "")
