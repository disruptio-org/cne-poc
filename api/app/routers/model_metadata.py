from __future__ import annotations

from fastapi import APIRouter

from ml.registry import ModelRegistry

from ..schemas import ModelHistoryResponse

router = APIRouter()
registry = ModelRegistry()


@router.get("/history", response_model=ModelHistoryResponse)
async def history() -> ModelHistoryResponse:
    return registry.history()
