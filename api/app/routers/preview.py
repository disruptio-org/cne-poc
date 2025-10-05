from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from ..schemas import PreviewResponse
from ..services.jobs import PROCESSED_DIR

router = APIRouter()


@router.get("/{job_id}", response_model=PreviewResponse)
async def get_preview(job_id: str) -> PreviewResponse:
    preview_path = PROCESSED_DIR / job_id / "preview.json"
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview not available")
    data = json.loads(preview_path.read_text(encoding="utf-8"))
    return PreviewResponse(**data)
