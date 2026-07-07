from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AcquisitionSourceRead(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    source_url: str
    source_name: str
    source_type: str
    description: str | None
    data_status: str
    data_confidence: float | None
    is_active: bool
    is_demo: bool
    robots_allowed: bool | None
    created_at: datetime

    class Config:
        from_attributes = True


class AcquisitionSourceCreate(BaseModel):
    institution_id: uuid.UUID
    source_url: str = Field(..., max_length=1000)
    source_name: str = Field(..., max_length=500)
    source_type: str = Field(default="official_website", max_length=100)
    description: str | None = None
    data_status: str = Field(default="needs_review")
    data_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AcquisitionJobRead(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    status: str
    documents_downloaded: int
    errors_count: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AcquisitionJobStart(BaseModel):
    institution_id: uuid.UUID
    source_ids: list[uuid.UUID] | None = None


class AcquisitionLogRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    source_url: str
    success: bool
    status_code: int | None
    file_type: str | None
    error_message: str | None
    robots_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DownloadedDocumentRead(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    source_url: str
    title: str
    file_type: str
    document_type: str
    data_status: str
    checksum: str | None
    is_duplicate: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcquisitionStatistics(BaseModel):
    institution_id: uuid.UUID | None
    total_sources: int
    active_sources: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_documents: int
    total_errors: int
    last_job_at: datetime | None
