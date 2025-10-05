from __future__ import annotations

import csv
import json
import logging
import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schemas import JobCreate, JobDetail, JobList, JobStatus, JobSummary
from .metrics import MetricsService
from ml.registry import ModelRegistry

LOGGER = logging.getLogger(__name__)
STATE_FILE = Path("data/state/jobs.json")
QUEUE_FILE = Path("data/state/queue.jsonl")
INCOMING_DIR = Path("data/incoming")
PROCESSED_DIR = Path("data/processed")
APPROVED_DIR = Path("data/approved")

for directory in (STATE_FILE.parent, INCOMING_DIR, PROCESSED_DIR, APPROVED_DIR):
    directory.mkdir(parents=True, exist_ok=True)


class JobService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics = MetricsService.get_instance()
        self._state: dict[str, dict[str, Any]] = {}
        if STATE_FILE.exists():
            self._state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str), encoding="utf-8")

    def create(self, payload: JobCreate) -> JobDetail:
        job_id = uuid.uuid4().hex
        now = datetime.utcnow().isoformat()
        record = {
            "job_id": job_id,
            "status": JobStatus.RECEIVED.value,
            "filename": payload.filename,
            "created_at": now,
            "updated_at": now,
            "metadata": {"uploader": payload.uploader},
            "preview_ready": False,
            "csv_ready": False,
            "error": None,
            "approved_at": None,
            "ocr_conf_mean": None,
        }
        with self._lock:
            self._state[job_id] = record
            self._persist()
        self._metrics.increment("jobs.created")
        LOGGER.info("Job %s received", job_id, extra={"job_id": job_id, "status": record["status"]})
        return JobDetail(**record)

    def list_jobs(self) -> JobList:
        with self._lock:
            jobs = [JobSummary(**data) for data in self._state.values()]
        jobs.sort(key=lambda job: job.created_at, reverse=True)
        return JobList(jobs=jobs)

    def get(self, job_id: str) -> JobDetail:
        with self._lock:
            data = self._state.get(job_id)
        if not data:
            raise KeyError(job_id)
        return JobDetail(**data)

    def update_status(self, job_id: str, status: JobStatus, **updates: Any) -> JobDetail:
        with self._lock:
            if job_id not in self._state:
                raise KeyError(job_id)
            record = self._state[job_id]
            metadata_update = updates.pop("metadata", None)
            if metadata_update is not None:
                merged_metadata = {**record.get("metadata", {}), **metadata_update}
                record["metadata"] = merged_metadata
                if "ocr_conf_mean" in metadata_update:
                    record["ocr_conf_mean"] = metadata_update["ocr_conf_mean"]
            record.update(updates)
            record["status"] = status.value
            record["updated_at"] = datetime.utcnow().isoformat()
            self._persist()
        LOGGER.info("Job %s status -> %s", job_id, status.value, extra={"job_id": job_id, "status": status.value})
        return JobDetail(**record)

    def mark_preview_ready(self, job_id: str) -> None:
        self.update_status(job_id, JobStatus.COMPLETED, preview_ready=True, csv_ready=True)

    def mark_failed(self, job_id: str, error: str) -> None:
        self.update_status(job_id, JobStatus.FAILED, error=error)

    def approve(self, job_id: str, approver: str, notes: str | None = None) -> JobDetail:
        detail = self.get(job_id)
        updated = self.update_status(
            job_id,
            JobStatus.APPROVED,
            approved_at=datetime.utcnow().isoformat(),
            metadata={**detail.metadata, "approved_by": approver, "notes": notes},
        )
        self._metrics.increment("jobs.approved")
        try:
            self._materialize_approval(job_id)
        except FileNotFoundError:
            LOGGER.warning("Approved job %s is missing processed artifacts", job_id)
        return updated

    def _materialize_approval(self, job_id: str) -> None:
        processed_dir = PROCESSED_DIR / job_id
        csv_src = processed_dir / "output.csv"
        if not csv_src.exists():
            raise FileNotFoundError(csv_src)
        approved_dir = APPROVED_DIR / job_id
        approved_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(csv_src, approved_dir / "output.csv")
        preview_src = processed_dir / "preview.json"
        if preview_src.exists():
            shutil.copy2(preview_src, approved_dir / "preview.json")
        self._register_candidate(job_id, csv_src)

    def _register_candidate(self, job_id: str, csv_path: Path) -> None:
        with csv_path.open(encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        metrics = {"rows": len(rows), "job_id": job_id}
        registry = ModelRegistry()
        registry.register(model_name=f"dataset-{job_id}", metrics=metrics, status="candidate")

    def record_error(self, job_id: str, error: str) -> None:
        LOGGER.error("Job %s failed: %s", job_id, error, extra={"job_id": job_id, "error": error})
        self.mark_failed(job_id, error)

    def enqueue(self, job: JobDetail) -> None:
        payload = {
            "job_id": job.job_id,
            "filename": job.filename,
            "received_at": job.created_at,
        }
        with QUEUE_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        self.update_status(job.job_id, JobStatus.QUEUED)
        self._metrics.increment("jobs.queued")
        LOGGER.info("Job %s enqueued", job.job_id, extra={"job_id": job.job_id})

    def set_processing(self, job_id: str) -> None:
        self.update_status(job_id, JobStatus.PROCESSING)
        self._metrics.increment("jobs.processing")

    def set_completed(self, job_id: str) -> None:
        self.update_status(job_id, JobStatus.COMPLETED, preview_ready=True, csv_ready=True)
        self._metrics.increment("jobs.completed")
