"""Schemas for audit runs, findings, and reports."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AuditRunStatus,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Finding schemas
# ---------------------------------------------------------------------------


class AuditFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_run_id: uuid.UUID
    finding_type: FindingType
    severity: FindingSeverity
    document_category: FileCategory | None
    file_id: uuid.UUID | None
    title: str
    description: str
    recommendation: str
    is_resolved: bool
    resolved_note: str | None
    created_at: datetime


class FindingResolveRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class AuditRunBrief(BaseModel):
    """Lightweight run info for history lists."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_type: str
    module_id: uuid.UUID | None       # None for programme/faculty-scoped runs
    programme_id: uuid.UUID | None    # None for module-scoped runs
    run_status: AuditRunStatus
    audit_status: AuditStatus | None
    compliance_score: float | None
    documents_present: int | None
    documents_missing: int | None
    triggered_by_id: uuid.UUID | None
    created_at: datetime
    completed_at: datetime | None


class AuditRunRead(AuditRunBrief):
    """Full run record including summary and findings."""

    institution_id: uuid.UUID
    total_required: int | None
    summary: str | None
    started_at: datetime | None
    error_message: str | None
    findings: list[AuditFindingRead]


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class AuditTriggerResponse(BaseModel):
    audit_run_id: uuid.UUID
    module_id: uuid.UUID
    run_status: AuditRunStatus
    message: str


# ---------------------------------------------------------------------------
# Report — full structured output for a single audit run
# ---------------------------------------------------------------------------


class DocumentPresenceItem(BaseModel):
    """One row in the 'documents present' section of the report."""

    category: FileCategory
    file_count: int
    latest_filename: str | None
    latest_uploaded_at: datetime | None


class MissingDocumentItem(BaseModel):
    """One row in the 'documents missing' section of the report."""

    category: FileCategory
    severity: FindingSeverity
    weight: int
    recommendation: str


class AuditReport(BaseModel):
    """Full structured report returned by ``GET /audits/{id}/report``."""

    # Run identity
    audit_run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    institution_id: uuid.UUID

    # Audit metadata
    run_status: AuditRunStatus
    triggered_by_id: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None

    # Compliance result
    audit_status: AuditStatus | None
    compliance_score: float | None = Field(default=None, ge=0.0, le=100.0)
    total_required: int | None
    documents_present_count: int | None
    documents_missing_count: int | None

    # Summary narrative
    summary: str | None

    # Detail tables
    documents_present: list[DocumentPresenceItem]
    documents_missing: list[MissingDocumentItem]

    # All findings ordered by severity
    findings: list[AuditFindingRead]

    # Counts by severity (for dashboard widgets)
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
