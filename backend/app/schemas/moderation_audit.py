"""Schemas for the Moderation Compliance Audit endpoints.

Mirrors ``schemas/assessment_audit.py`` (Stage 8) structurally — same
two-component score breakdown and per-document quality shapes — plus a
``DateSequenceInfo`` block specific to the moderation date-sequencing check
(item 12 of the SRS checklist).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentType,
    AuditRunStatus,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class ModerationFindingRead(BaseModel):
    """An individual finding from a moderation compliance run."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_run_id: uuid.UUID
    finding_type: FindingType
    severity: FindingSeverity
    document_category: FileCategory | None = None
    file_id: uuid.UUID | None = None
    title: str
    description: str
    recommendation: str
    is_resolved: bool
    resolved_note: str | None = None
    created_at: datetime


class FindingResolveRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


# ---------------------------------------------------------------------------
# Document quality breakdown
# ---------------------------------------------------------------------------


class ProbeResultRead(BaseModel):
    """Pass/fail outcome for one TextProbe against one document."""

    probe_id: str
    label: str
    passed: bool
    severity: FindingSeverity
    weight: float


class DocumentQualityBreakdown(BaseModel):
    """Quality probe summary for a single document in a moderation run."""

    file_id: uuid.UUID
    filename: str
    category: FileCategory
    has_extraction: bool
    probes_run: int
    probes_passed: int
    quality_score: float = Field(
        description="0-100: percentage of weighted probe weight passed.",
        ge=0.0,
        le=100.0,
    )
    probe_results: list[ProbeResultRead]


# ---------------------------------------------------------------------------
# Date-sequencing check (item 12)
# ---------------------------------------------------------------------------


class DateSequenceInfo(BaseModel):
    """Result of comparing the moderation date against the assessment release date."""

    evaluated: bool = Field(
        description="False if either date could not be determined from the documents."
    )
    passed: bool = Field(
        description="True if moderation occurred on/before the assessment release date "
        "(or the check could not be evaluated)."
    )
    moderation_date: date | None = None
    assessment_release_date: date | None = None


# ---------------------------------------------------------------------------
# Presence checklist summary
# ---------------------------------------------------------------------------


class ModerationDocumentItem(BaseModel):
    """One required moderation document and its compliance status."""

    category: FileCategory
    label: str
    severity: FindingSeverity
    weight: int
    present: bool


# ---------------------------------------------------------------------------
# Full moderation compliance report
# ---------------------------------------------------------------------------


class ModerationComplianceReport(BaseModel):
    """Full structured report for a completed moderation compliance run.

    Returned by GET /moderation-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    academic_year: str

    presence_score: float = Field(description="Weighted document presence score (0-100).")
    quality_score: float = Field(description="Weighted content quality probe score (0-100).")
    overall_score: float = Field(description="Combined score: 60% presence + 40% quality (0-100).")
    audit_status: AuditStatus

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_probes: int
    passed_quality_probes: int

    documents_present: list[ModerationDocumentItem]
    documents_missing: list[ModerationDocumentItem]

    document_quality: list[DocumentQualityBreakdown]
    date_sequence: DateSequenceInfo

    findings: list[ModerationFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class ModerationRunBrief(BaseModel):
    """Lightweight run info for history lists."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    module_id: uuid.UUID
    agent_type: AgentType
    run_status: AuditRunStatus
    audit_status: AuditStatus | None = None
    overall_score: float | None = Field(default=None, alias="compliance_score")
    documents_present: int | None = None
    documents_missing: int | None = None
    triggered_by_id: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class ModerationRunRead(BaseModel):
    """Full audit run with findings list (no quality breakdown; use /report for that)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    institution_id: uuid.UUID
    agent_type: AgentType
    run_status: AuditRunStatus
    audit_status: AuditStatus | None = None
    compliance_score: float | None = None
    documents_present: int | None = None
    documents_missing: int | None = None
    total_required: int | None = None
    summary: str | None = None
    error_message: str | None = None
    triggered_by_id: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    findings: list[ModerationFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class ModerationTriggerResponse(BaseModel):
    """Returned immediately when a moderation audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
