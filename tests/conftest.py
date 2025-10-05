from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Callable
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from api.app.schemas import JobCreate
from api.app.services import jobs as jobs_module
from api.app.services.jobs import JobService
from worker.src import fuzzy

BASE_DOCUMENT = """CNE Diário Oficial
orgao: Conselho Nacional de Educação
lista: Lista Unica
tipo: Titular
sigla: Mec
descricao: Representante titular unico
valor: 1000
fonte: DOU
competencia: 2024
observacao: Nomeacao publicada

orgao: Conselho Nacional de Educação
lista: Coligacao Educação & Cidadania
tipo: Titular
sigla: inep
descricao: Titular coligacao com simbolos
valor: 950
fonte: DOU
competencia: 2024
observacao: Mantem coligacao

orgao: Conselho Nacional de Educação
lista: Lista Unica
tipo: Suplente
descricao: Suplente aguardando confirmacao
valor: 0
fonte: DOU
competencia: 2024
observacao: OCR incerta

orgao: Conselho Nacional de Educação
lista: Grupo GCE § Educação
tipo: GCE
sigla: GCE
descricao: Grupo consultivo especial
valor: 0
fonte: Memo Nº 10
competencia: 2024
observacao: Representacao simbolica
"""


@pytest.fixture(autouse=True)
def reset_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    from api.app.services import metrics

    monkeypatch.setattr(metrics.MetricsService, "_instance", None)


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    data_dir = tmp_path / "data"
    incoming = data_dir / "incoming"
    processed = data_dir / "processed"
    approved = data_dir / "approved"
    state_dir = data_dir / "state"
    master_dir = data_dir / "master"
    for directory in (incoming, processed, approved, state_dir, master_dir):
        directory.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(jobs_module, "STATE_FILE", state_dir / "jobs.json")
    monkeypatch.setattr(jobs_module, "QUEUE_FILE", state_dir / "queue.jsonl")
    monkeypatch.setattr(jobs_module, "INCOMING_DIR", incoming)
    monkeypatch.setattr(jobs_module, "PROCESSED_DIR", processed)
    monkeypatch.setattr(jobs_module, "APPROVED_DIR", approved)
    monkeypatch.setattr(jobs_module, "MASTER_DATA_DIR", master_dir)
    monkeypatch.setattr(jobs_module, "_EVENT_LISTENERS", defaultdict(list))
    for directory in (jobs_module.STATE_FILE.parent, incoming, processed, approved):
        directory.mkdir(parents=True, exist_ok=True)

    import worker.src.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "INCOMING_DIR", incoming)
    monkeypatch.setattr(pipeline_module, "PROCESSED_DIR", processed)

    import ml.registry as registry_module

    registry_module.REGISTRY_FILE = state_dir / "model_registry.json"
    registry_module.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

    import api.app.services.master_data as master_data_module

    monkeypatch.setattr(master_data_module, "DATA_DIR", master_dir)

    return SimpleNamespace(incoming=incoming, processed=processed, approved=approved, state=state_dir)


@pytest.fixture(autouse=True)
def synthetic_master_data(monkeypatch: pytest.MonkeyPatch) -> None:
    master_cache = {
        "MEC": {"sigla": "MEC", "descricao": "Ministério da Educação", "codigo": "001"},
        "INEP": {
            "sigla": "INEP",
            "descricao": "Instituto Nacional de Estudos e Pesquisas Educacionais",
            "codigo": "002",
        },
        "GCE": {"sigla": "GCE", "descricao": "Grupo Consultivo Especial", "codigo": "003"},
    }
    monkeypatch.setattr(fuzzy, "MASTER_CACHE", master_cache)


@pytest.fixture
def job_service() -> JobService:
    return JobService()


@pytest.fixture
def job_factory(job_service: JobService) -> Callable[[Path], str]:
    def _create_job(source_path: Path) -> str:
        job = job_service.create(JobCreate(filename=source_path.name, uploader="pytest"))
        job_dir = jobs_module.INCOMING_DIR / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        destination = job_dir / source_path.name
        shutil.copy2(source_path, destination)
        return job.job_id

    return _create_job


@pytest.fixture
def pdf_sample(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    path.write_text(BASE_DOCUMENT, encoding="utf-8")
    return path


@pytest.fixture
def docx_sample(tmp_path: Path) -> Path:
    path = tmp_path / "sample.docx"
    path.write_text(BASE_DOCUMENT.replace("descrição", "descricao"), encoding="utf-8")
    return path


@pytest.fixture
def xlsx_sample(tmp_path: Path) -> Path:
    path = tmp_path / "sample.xlsx"
    path.write_text(BASE_DOCUMENT, encoding="utf-8")
    return path


@pytest.fixture
def zip_sample(tmp_path: Path) -> Path:
    archive_path = tmp_path / "sample.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("document.txt", BASE_DOCUMENT)
    return archive_path


@pytest.fixture
def golden_rows() -> list[dict[str, str]]:
    golden_path = Path("samples/golden/example_output.csv")
    with golden_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


@pytest.fixture
def preview_loader() -> Callable[[Path], dict]:
    def _load_preview(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    return _load_preview
