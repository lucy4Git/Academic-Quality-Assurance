"""Schemas for the Evidence Verification Audit endpoints.

Mirrors ``schemas/attendance_audit.py`` (Stage 10) structurally — the same
two-component score breakdown and per-document quality shapes — plus
cross-agent support-check results (items 8/9/10) and duplicate/conflicting
evidence groups (item 11) specific to evidence verification.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentType,
    AuditRunStatus,
    AuditStatus,
    EvidenceRiskLevel,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class EvidenceFindingRead(BaseModel):
    """An individual finding from an evidence verification run."""

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
    """Pass/fail outcome for one probe against one document."""

    probe_id: str
    label: str
    passed: bool
    severity: FindingSeverity
    weight: float


class DocumentQualityBreakdown(BaseModel):
    """Quality probe summary for a single document in an evidence run."""

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
    module_link_passed: bool | None = Field(
        default=None,
        description="Whether the document references the correct module (item 2).",
    )
    assessment_link_passed: bool | None = Field(
        default=None,
        description=(
            "Whether the document references a defined assessment (item 3). "
            "Null if not applicable to this document's category."
        ),
    )


# ---------------------------------------------------------------------------
# Cross-agent support checks (items 8/9/10)
# ---------------------------------------------------------------------------


class CrossCheckRead(BaseModel):
    """Result of one cross-agent evidence-support check."""

    check_id: str
    label: str
    applicable: bool
    passed: bool


# ---------------------------------------------------------------------------
# Duplicate / conflicting evidence (item 11)
# ---------------------------------------------------------------------------


class DuplicateGroupRead(BaseModel):
    """A group of files that are duplicates (same checksum) or conflicting
    versions (same single-instance category, different checksums)."""

    file_ids: list[uuid.UUID]
    filenames: list[str]
    categories: list[FileCategory]


# ---------------------------------------------------------------------------
# Presence checklist summary
# ---------------------------------------------------------------------------


class EvidenceGroupItem(BaseModel):
    """One required evidence group and its compliance status."""

    group_id: str
    label: str
    categories: list[FileCategory]
    severity: FindingSeverity
    weight: int
    present: bool


# ---------------------------------------------------------------------------
# Full evidence verification report
# ---------------------------------------------------------------------------


class EvidenceVerificationReport(BaseModel):
    """Full structured report for a completed evidence verification run.

    Returned by GET /evidence-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    academic_year: str

    presence_score: float = Field(description="Weighted evidence-group presence score (0-100).")
    quality_score: float = Field(description="Weighted content/linkage quality probe score (0-100).")
    overall_score: float = Field(description="Combined score: 60% presence + 40% quality (0-100).")
    audit_status: AuditStatus
    risk_level: EvidenceRiskLevel = Field(
        description="Evidence risk level derived from completeness and overall score."
    )
    completeness_percentage: float = Field(
        description="0-100: percentage of required evidence groups present.",
        ge=0.0,
        le=100.0,
    )

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_weight: float
    achieved_quality_weight: float

    evidence_groups: list[EvidenceGroupItem]
    document_quality: list[DocumentQualityBreakdown]
    cross_checks: list[CrossCheckRead]
    duplicate_groups: list[DuplicateGroupRead]
    conflicting_groups: list[DuplicateGroupRead]

    findings: list[EvidenceFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class EvidenceRunBrief(BaseModel):
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


class EvidenceRunRead(BaseModel):
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
    findings: list[EvidenceFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class EvidenceTriggerResponse(BaseModel):
    """Returned immediately when an evidence verification audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
