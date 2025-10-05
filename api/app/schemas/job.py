from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    RECEIVED = "received"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"


class JobCreate(BaseModel):
    filename: str
    uploader: Optional[str] = Field(default=None, description="Name or identifier of the uploader")


class JobSummary(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    ocr_conf_mean: Optional[float] = Field(
        default=None,
        description="Average OCR confidence score for processed documents.",
    )


class JobDetail(JobSummary):
    metadata: dict[str, Any] = Field(default_factory=dict)
    preview_ready: bool = False
    csv_ready: bool = False
    approved_at: Optional[datetime] = None


class JobList(BaseModel):
    jobs: list[JobSummary]
