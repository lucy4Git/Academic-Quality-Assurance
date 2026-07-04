"""Schemas for DocumentRecord — processing status and extraction results."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FileCategory, ProcessingStatus


class DocumentRecordRead(BaseModel):
    """Full processing record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    institution_id: uuid.UUID
    status: ProcessingStatus
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    word_count: int | None
    page_count: int | None
    language_detected: str | None
    classification: FileCategory | None
    classification_confidence: float | None
    metadata_json: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentRecordBrief(BaseModel):
    """Lightweight record for list endpoints (excludes extracted_text)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    status: ProcessingStatus
    word_count: int | None
    page_count: int | None
    classification: FileCategory | None
    classification_confidence: float | None
    created_at: datetime
    updated_at: datetime


class DocumentRecordWithText(DocumentRecordRead):
    """Includes the full extracted text — only returned on explicit request."""

    extracted_text: str | None


class ProcessingTriggerResponse(BaseModel):
    """Returned when processing is triggered for a file."""

    file_id: uuid.UUID
    record_id: uuid.UUID
    status: ProcessingStatus
    message: str


class ReclassifyResponse(BaseModel):
    """Returned after a reclassification run."""

    file_id: uuid.UUID
    record_id: uuid.UUID
    previous_classification: FileCategory | None
    new_classification: FileCategory | None
    confidence: float | None = Field(ge=0.0, le=1.0, default=None)
