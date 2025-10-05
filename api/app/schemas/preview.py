from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationBadge(BaseModel):
    field: str
    status: str
    message: str | None = None


class PreviewRow(BaseModel):
    columns: list[str]
    validations: list[ValidationBadge] = Field(default_factory=list)


class PreviewResponse(BaseModel):
    job_id: str
    headers: list[str]
    rows: list[PreviewRow]
    total_rows: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class CsvDownload(BaseModel):
    job_id: str
    url: str


class ApprovalRequest(BaseModel):
    approver: str
    notes: str | None = None


class ApprovalResponse(BaseModel):
    job_id: str
    approved: bool
    approved_at: str
    notes: str | None = None


class MasterRecord(BaseModel):
    sigla: str
    descricao: str
    codigo: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MasterDataResponse(BaseModel):
    records: list[MasterRecord]


class ModelMetadata(BaseModel):
    model_name: str
    version: str
    created_at: str
    status: str
    metrics: dict[str, Any]


class ModelHistoryResponse(BaseModel):
    items: list[ModelMetadata]
