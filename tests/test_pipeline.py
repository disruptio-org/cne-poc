from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pytest

from api.app.schemas import ApprovalRequest
from api.app.services import jobs as jobs_module
from worker.src.pipeline import process_job


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


@pytest.mark.parametrize(
    "fixture_name",
    ["pdf_sample", "docx_sample", "xlsx_sample", "zip_sample"],
)
def test_pipeline_outputs_match_golden(
    fixture_name: str,
    request: pytest.FixtureRequest,
    job_factory,
    golden_rows,
    preview_loader,
) -> None:
    source_path: Path = request.getfixturevalue(fixture_name)
    job_id = job_factory(source_path)
    process_job(job_id)

    csv_path = jobs_module.PROCESSED_DIR / job_id / "output.csv"
    assert csv_path.exists(), "Processed CSV should be generated"
    actual_rows = _load_csv(csv_path)
    assert actual_rows == golden_rows

    counters: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for row in actual_rows:
        key = (
            row.get("dtmnfr", ""),
            row.get("orgao", "").upper(),
            row.get("sigla", "").upper(),
            row.get("lista", "").upper(),
            row.get("tipo", "").upper(),
        )
        counters[key] += 1
        assert row["num_ordem"] == str(counters[key])
        counters[row["TIPO"]] += 1
        assert row["NUM_ORDEM"] == str(counters[row["TIPO"]])

    preview_path = jobs_module.PROCESSED_DIR / job_id / "preview.json"
    preview = preview_loader(preview_path)
    assert preview["total_rows"] == len(golden_rows)
    assert preview["headers"][6] == "NUM_ORDEM"
    sigla_statuses = []
    for row in preview["rows"]:
        statuses = {badge["field"]: badge["status"] for badge in row["validations"]}
        assert statuses.get("orgao") == "ok"
        assert statuses.get("lista") in {"ok", "aviso"}
        assert statuses.get("tipo") == "ok"
        sigla_statuses.append(statuses.get("sigla"))
    assert "aviso" in sigla_statuses, "Rows with missing sigla should emit avisos"
        assert statuses.get("ORGAO") == "ok"
        assert statuses.get("NOME_LISTA") == "ok"
        assert statuses.get("TIPO") == "ok"
        sigla_statuses.append(statuses.get("SIGLA"))
    assert "warning" in sigla_statuses, "Rows with missing sigla should emit warnings"


@pytest.mark.parametrize("fixture_name", ["pdf_sample", "zip_sample"])
def test_low_confidence_rows_flagged(
    fixture_name: str,
    request: pytest.FixtureRequest,
    job_factory,
) -> None:
    job_id = job_factory(request.getfixturevalue(fixture_name))
    process_job(job_id)
    preview_path = jobs_module.PROCESSED_DIR / job_id / "preview.json"
    data = json.loads(preview_path.read_text(encoding="utf-8"))
    low_confidence_rows = [
        row for row in data["rows"] if any(badge["status"] == "aviso" for badge in row["validations"])
    ]
    assert low_confidence_rows, "Expected at least one row flagged with low confidence warnings"


def test_approval_promotes_artifacts(
    job_factory,
    job_service: jobs_module.JobService,
    golden_rows,
    pdf_sample: Path,
    isolated_data_dirs,
) -> None:
    job_id = job_factory(pdf_sample)
    process_job(job_id)

    approval_request = ApprovalRequest(approver="admin", notes="ok")
    job_service.approve(job_id, approver=approval_request.approver, notes=approval_request.notes)

    approved_job = job_service.get(job_id)
    assert approved_job.approved_at is not None
    approved_at = approved_job.approved_at
    if isinstance(approved_at, str):
        approved_at = datetime.fromisoformat(approved_at)
    approved_date = approved_at.strftime("%Y-%m-%d")
    approval_dir = jobs_module.APPROVED_DIR / approved_date / job_id
    assert approval_dir.exists(), "Approved directory should include date partition"

    approved_csv = approval_dir / "output.csv"
    assert approved_csv.exists(), "Approved CSV should be copied to the approved directory"
    assert _load_csv(approved_csv) == golden_rows

    preview_path = approval_dir / "preview.json"
    assert preview_path.exists(), "Preview JSON should be copied to the approved directory"

    uploads_dir = approval_dir / "incoming"
    assert uploads_dir.exists(), "Incoming uploads should be preserved"
    original_uploads = list(uploads_dir.iterdir())
    assert original_uploads, "Original uploads should be copied"
    assert original_uploads[0].read_bytes() == pdf_sample.read_bytes()

    meta_path = approval_dir / "meta.json"
    assert meta_path.exists(), "meta.json should be written for approved jobs"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["job"]["job_id"] == job_id
    assert meta["job"]["metadata"]["approved_by"] == approval_request.approver
    assert meta["versions"]["model"]["version"], "Model version should be recorded"
    assert meta["versions"]["master_data"] == job_service._master_data_version()  # type: ignore[attr-defined]

    registry_file = isolated_data_dirs.state / "model_registry.json"
    assert registry_file.exists()
    history = json.loads(registry_file.read_text(encoding="utf-8"))
    assert history, "Model registry should contain at least one candidate entry"
    latest = history[-1]
    assert latest["model_name"] == f"dataset-{job_id}"
    assert latest["status"] == "candidate"
    assert latest["metrics"]["rows"] == len(golden_rows)


def test_approval_emits_event(
    job_factory,
    job_service: jobs_module.JobService,
    pdf_sample: Path,
    isolated_data_dirs,
) -> None:
    events: list[dict] = []

    def _listener(payload: dict) -> None:
        events.append(payload)

    jobs_module.subscribe("result.approved", _listener)

    job_id = job_factory(pdf_sample)
    process_job(job_id)
    approval_request = ApprovalRequest(approver="listener", notes=None)
    job_service.approve(job_id, approver=approval_request.approver, notes=approval_request.notes)

    assert events, "result.approved event should be emitted"
    payload = events[0]
    assert payload["meta"]["job"]["job_id"] == job_id
    assert Path(payload["path"]).exists()
