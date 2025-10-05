from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import ApprovalRequest, ApprovalResponse
from ..services.jobs import JobService

router = APIRouter()
service = JobService()


@router.post("/{job_id}", response_model=ApprovalResponse)
async def approve_job(job_id: str, payload: ApprovalRequest) -> ApprovalResponse:
    try:
        job = service.approve(job_id, approver=payload.approver, notes=payload.notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    return ApprovalResponse(
        job_id=job.job_id,
        approved=True,
        approved_at=job.approved_at or "",
        notes=payload.notes,
    )
