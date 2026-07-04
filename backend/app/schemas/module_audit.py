"""Module Folder Audit request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ChecklistItemStatus, ModuleAuditStatus


# ---------------------------------------------------------------------------
# Checklist item schemas
# ---------------------------------------------------------------------------


class ChecklistItemUpdate(BaseModel):
    """Payload to update a single checklist item."""

    status: ChecklistItemStatus
    comment: str | None = Field(default=None, max_length=1000)
    evidence_required: bool = True


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_id: uuid.UUID
    item_key: str
    item_label: str
    status: ChecklistItemStatus
    comment: str | None
    evidence_required: bool
    updated_at: datetime


# ---------------------------------------------------------------------------
# Module audit schemas
# ---------------------------------------------------------------------------


class ModuleAuditCreate(BaseModel):
    """Create a new audit for a module."""

    module_id: uuid.UUID
    academic_year: str = Field(min_length=9, max_length=9)
    notes: str | None = Field(default=None, max_length=2000)


class ModuleAuditUpdate(BaseModel):
    """Patch fields and/or submit checklist updates."""

    notes: str | None = Field(default=None, max_length=2000)
    # Optional bulk checklist update: {item_key: ChecklistItemUpdate}
    checklist: dict[str, ChecklistItemUpdate] | None = None


class ModuleAuditBrief(BaseModel):
    """Lightweight audit summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    institution_id: uuid.UUID
    faculty_id: uuid.UUID
    department_id: uuid.UUID
    programme_id: uuid.UUID
    auditor_id: uuid.UUID | None
    academic_year: str
    status: ModuleAuditStatus
    total_items: int
    compliant_count: int
    missing_count: int
    partial_count: int
    not_applicable_count: int
    compliance_percentage: float
    created_at: datetime
    updated_at: datetime


class ModuleAuditRead(ModuleAuditBrief):
    """Full audit record including checklist."""

    notes: str | None
    checklist_items: list[ChecklistItemRead]
