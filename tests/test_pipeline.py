from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import pytest

from api.app.schemas import ApprovalRequest
from api.app.services import jobs as jobs_module
from worker.src.pipeline import process_job


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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

    counters: dict[str, int] = defaultdict(int)
    for row in actual_rows:
        counters[row["tipo"]] += 1
        assert row["num_ordem"] == str(counters[row["tipo"]])

    preview_path = jobs_module.PROCESSED_DIR / job_id / "preview.json"
    preview = preview_loader(preview_path)
    assert preview["total_rows"] == len(golden_rows)
    assert preview["headers"][3] == "num_ordem"
    assert "metadata" in preview
    assert "ocr_conf_mean" in preview["metadata"]
    assert 0.0 <= preview["metadata"]["ocr_conf_mean"] <= 1.0
    sigla_statuses = []
    for row in preview["rows"]:
        statuses = {badge["field"]: badge["status"] for badge in row["validations"]}
        assert statuses.get("orgao") == "ok"
        assert statuses.get("lista") == "ok"
        assert statuses.get("tipo") == "ok"
        sigla_statuses.append(statuses.get("sigla"))
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
        row for row in data["rows"] if any(badge["status"] == "warning" for badge in row["validations"])
    ]
    assert low_confidence_rows, "Expected at least one row flagged with low confidence warnings"


def test_ocr_confidence_persisted(
    pdf_sample: Path,
    job_factory,
    preview_loader,
) -> None:
    job_id = job_factory(pdf_sample)
    process_job(job_id)

    preview_path = jobs_module.PROCESSED_DIR / job_id / "preview.json"
    preview = preview_loader(preview_path)
    conf_from_preview = preview["metadata"]["ocr_conf_mean"]

    detail = jobs_module.JobService().get(job_id)
    assert detail.metadata.get("ocr_conf_mean") == pytest.approx(conf_from_preview)
    assert detail.ocr_conf_mean == pytest.approx(conf_from_preview)


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

    approved_csv = jobs_module.APPROVED_DIR / job_id / "output.csv"
    assert approved_csv.exists(), "Approved CSV should be copied to the approved directory"
    assert _load_csv(approved_csv) == golden_rows

    registry_file = isolated_data_dirs.state / "model_registry.json"
    assert registry_file.exists()
    history = json.loads(registry_file.read_text(encoding="utf-8"))
    assert history, "Model registry should contain at least one candidate entry"
    latest = history[-1]
    assert latest["model_name"] == f"dataset-{job_id}"
    assert latest["status"] == "candidate"
    assert latest["metrics"]["rows"] == len(golden_rows)
