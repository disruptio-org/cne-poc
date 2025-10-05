from __future__ import annotations

from fastapi import APIRouter

from ..schemas import MasterDataResponse, MasterRecord
from ..services.master_data import MasterDataService

router = APIRouter()
service = MasterDataService()


@router.get("/", response_model=MasterDataResponse)
async def list_master_data() -> MasterDataResponse:
    return service.list_records()


@router.post("/", response_model=MasterRecord)
async def upsert_master_record(record: MasterRecord) -> MasterRecord:
    service.upsert(record)
    return record
