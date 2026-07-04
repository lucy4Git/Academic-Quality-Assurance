"""AuditEvidence request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    module_id: uuid.UUID
    audit_id: uuid.UUID
    checklist_item_id: uuid.UUID | None
    uploaded_by_id: uuid.UUID | None

    original_filename: str
    mime_type: str
    file_size_bytes: int
    evidence_category: str
    description: str | None

    created_at: datetime
    updated_at: datetime


class AuditEvidenceCreate(BaseModel):
    """Populated server-side from the multipart upload; not sent by the client directly."""

    audit_id: uuid.UUID
    checklist_item_id: uuid.UUID | None = None
    evidence_category: str = Field(default="general", max_length=80)
    description: str | None = Field(default=None, max_length=500)
