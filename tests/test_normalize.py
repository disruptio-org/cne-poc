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
        {"orgao": "Conselho", "lista": "Lista Única", "tipo": "Titular", "sigla": "mec", "dtmnfr": "2024-01-01"},
        {"orgao": "Conselho", "lista": "Lista Única", "tipo": "Titular", "sigla": "mec", "dtmnfr": "2024-01-01"},
        {"orgao": "Conselho", "lista": "Coligação", "tipo": "Titular", "sigla": "mec", "dtmnfr": "2024-01-01"},
        {"orgao": "Conselho", "lista": "Lista Única", "tipo": "Titular", "sigla": "mec", "dtmnfr": "2024-01-02"},
        {"orgao": "Conselho", "lista": "Lista Única", "tipo": "Suplente", "sigla": "mec", "dtmnfr": "2024-01-02"},
        {"orgao": "Conselho", "lista": "Lista Única", "tipo": "Titular", "sigla": "mec", "dtmnfr": "2024-01-01"},
    ]

    normalized = normalize.normalize(records)

    expected = ["1", "2", "1", "1", "1", "3"]
    assert [entry["num_ordem"] for entry in normalized] == expected
