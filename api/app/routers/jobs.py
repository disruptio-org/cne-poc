from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..schemas import JobCreate, JobDetail, JobList
from ..services.jobs import INCOMING_DIR, JobService

LOGGER = logging.getLogger(__name__)

router = APIRouter()
job_service = JobService()


@router.get("/", response_model=JobList)
async def list_jobs() -> JobList:
    return job_service.list_jobs()


@router.post("/", response_model=JobDetail)
async def create_job(
    file: UploadFile = File(...),
    uploader: str | None = Form(default=None),
) -> JobDetail:
    job = job_service.create(JobCreate(filename=file.filename, uploader=uploader))
    target_dir = INCOMING_DIR / job.job_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / file.filename
    contents = await file.read()
    target_file.write_bytes(contents)
    LOGGER.info("Stored upload for job %s at %s", job.job_id, target_file)
    job_service.enqueue(job)
    return job


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str) -> JobDetail:
    try:
        return job_service.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
