from __future__ import annotations

import logging
from pathlib import Path

from api.app.schemas import PreviewResponse, PreviewRow
from api.app.services.jobs import INCOMING_DIR, PROCESSED_DIR, JobService
from api.app.services.metrics import MetricsService

from . import csv_writer, extract, layout, normalize, ocr, segment, validate

LOGGER = logging.getLogger(__name__)


def _first_file(job_dir: Path) -> Path:
    for file in job_dir.iterdir():
        if file.is_file():
            return file
    raise FileNotFoundError(f"No files found in {job_dir}")


def process_job(job_id: str) -> None:
    job_service = JobService()
    metrics = MetricsService.get_instance()
    incoming_dir = INCOMING_DIR / job_id
    processed_dir = PROCESSED_DIR / job_id
    try:
        job_service.set_processing(job_id)
        file_path = _first_file(incoming_dir)
        LOGGER.info("Processing job %s from %s", job_id, file_path)
        lines = list(ocr.run_ocr(file_path))
        layout_info = layout.detect_layout(lines)
        segments = segment.segment_lines(layout_info)
        raw_records = extract.extract_records(segments)
        normalized_records = normalize.normalize(raw_records)
        validations = validate.validate(normalized_records)
        csv_writer.write_csv(job_id, normalized_records, PROCESSED_DIR)
        preview_rows = [
            PreviewRow(
                columns=[record.get(column, "") for column in extract.EXPECTED_COLUMNS],
                validations=row_badges,
            )
            for record, row_badges in zip(normalized_records, validations)
        ]
        preview = PreviewResponse(
            job_id=job_id,
            headers=extract.EXPECTED_COLUMNS,
            rows=preview_rows,
            total_rows=len(preview_rows),
        )
        processed_dir.mkdir(parents=True, exist_ok=True)
        preview_path = processed_dir / "preview.json"
        preview_path.write_text(preview.json(indent=2, ensure_ascii=False), encoding="utf-8")
        LOGGER.info("Job %s processed successfully", job_id)
        job_service.set_completed(job_id)
        metrics.increment("worker.jobs.completed")
    except Exception as exc:  # pragma: no cover - defensive flow
        LOGGER.exception("Job %s failed", job_id)
        job_service.record_error(job_id, str(exc))
        metrics.increment("worker.jobs.failed")
        raise
