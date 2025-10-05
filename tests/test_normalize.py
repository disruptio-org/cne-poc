from __future__ import annotations

from typing import Any

import pytest

from worker.src import normalize


@pytest.fixture(autouse=True)
def stub_match_sigla(monkeypatch: pytest.MonkeyPatch) -> None:
    def _identity(sigla: str) -> tuple[str, dict[str, Any] | None]:
        return sigla.upper(), None

    monkeypatch.setattr(normalize, "match_sigla", _identity)


def test_counter_resets_by_context() -> None:
    records = [
        {"DTMNFR": "2024-01-01", "ORGAO": "Conselho", "NOME_LISTA": "Lista Única", "TIPO": "Titular", "SIGLA": "mec"},
        {"DTMNFR": "2024-01-01", "ORGAO": "Conselho", "NOME_LISTA": "Lista Única", "TIPO": "Titular", "SIGLA": "mec"},
        {"DTMNFR": "2024-01-01", "ORGAO": "Conselho", "NOME_LISTA": "Coligação", "TIPO": "Titular", "SIGLA": "mec"},
        {"DTMNFR": "2024-01-02", "ORGAO": "Conselho", "NOME_LISTA": "Lista Única", "TIPO": "Titular", "SIGLA": "mec"},
        {"DTMNFR": "2024-01-02", "ORGAO": "Conselho", "NOME_LISTA": "Lista Única", "TIPO": "Suplente", "SIGLA": "mec"},
        {"DTMNFR": "2024-01-01", "ORGAO": "Conselho", "NOME_LISTA": "Lista Única", "TIPO": "Titular", "SIGLA": "mec"},
    ]

    normalized = normalize.normalize(records)

    expected = ["1", "2", "1", "1", "1", "3"]
    assert [entry["NUM_ORDEM"] for entry in normalized] == expected
