"""Schemas for the Attendance Compliance Audit endpoints.

Mirrors ``schemas/moderation_audit.py`` (Stage 9) structurally — same
two-component score breakdown and per-document quality shapes — plus a
``WeeklyCoverageInfo`` block specific to the attendance weekly-coverage
analysis (items 2/9/11) and an ``AttendanceRiskLevel`` field (item 12).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentType,
    AttendanceRiskLevel,
    AuditRunStatus,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class AttendanceFindingRead(BaseModel):
    """An individual finding from an attendance compliance run."""

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
    """Quality probe summary for a single document in an attendance run."""

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
# Weekly coverage analysis (items 2/9/11)
# ---------------------------------------------------------------------------


class WeeklyCoverageInfo(BaseModel):
    """Result of the weekly attendance-evidence coverage analysis."""

    expected_total_weeks: int = Field(
        description="Number of teaching weeks the module is expected to cover."
    )
    covered_weeks: list[int] = Field(
        description="Week numbers (1-N) for which attendance evidence was found."
    )
    missing_weeks: list[int] = Field(
        description="Week numbers (1-N) for which no attendance evidence was found."
    )
    completeness_percentage: float = Field(
        description="0-100: percentage of expected teaching weeks with evidence.",
        ge=0.0,
        le=100.0,
    )
    sources_evaluated: list[FileCategory] = Field(
        description="Document categories that contributed week-number data."
    )


# ---------------------------------------------------------------------------
# Presence checklist summary
# ---------------------------------------------------------------------------


class AttendanceDocumentItem(BaseModel):
    """One required attendance document and its compliance status."""

    category: FileCategory
    label: str
    severity: FindingSeverity
    weight: int
    present: bool


# ---------------------------------------------------------------------------
# Full attendance compliance report
# ---------------------------------------------------------------------------


class AttendanceComplianceReport(BaseModel):
    """Full structured report for a completed attendance compliance run.

    Returned by GET /attendance-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    academic_year: str

    presence_score: float = Field(description="Weighted document presence score (0-100).")
    quality_score: float = Field(description="Weighted content quality probe score (0-100).")
    overall_score: float = Field(description="Combined score: 60% presence + 40% quality (0-100).")
    audit_status: AuditStatus
    risk_level: AttendanceRiskLevel = Field(
        description="Attendance risk level derived from weekly coverage and overall score."
    )

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_probes: int
    passed_quality_probes: int

    documents_present: list[AttendanceDocumentItem]
    documents_missing: list[AttendanceDocumentItem]

    document_quality: list[DocumentQualityBreakdown]
    weekly_coverage: WeeklyCoverageInfo

    findings: list[AttendanceFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class AttendanceRunBrief(BaseModel):
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


class AttendanceRunRead(BaseModel):
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
    findings: list[AttendanceFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class AttendanceTriggerResponse(BaseModel):
    """Returned immediately when an attendance audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
