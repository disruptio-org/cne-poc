from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..services.jobs import PROCESSED_DIR

router = APIRouter()


@router.get("/{job_id}")
async def download_csv(job_id: str) -> FileResponse:
    csv_path = PROCESSED_DIR / job_id / "output.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not available")
    return FileResponse(csv_path, media_type="text/csv", filename=f"{job_id}.csv")
