"""Schemas for the Programme Review Audit endpoints (Stage 14).

Mirrors ``schemas/accreditation_readiness.py`` (Stage 13) structurally --
the same two-component score breakdown shape -- plus the per-module
breakdown, findings summary, gaps, and recommendations specific to
programme-level review.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentType,
    AuditRunStatus,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
    ReadinessRiskLevel,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class ProgrammeFindingRead(BaseModel):
    """An individual finding from a programme review run."""

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
# Per-module breakdown (item 1, 5)
# ---------------------------------------------------------------------------


class ModuleReviewRead(BaseModel):
    """Review summary for one module within the programme."""

    module_id: uuid.UUID
    module_label: str
    has_data: bool
    compliance_score: float | None = Field(
        default=None, description="Stage 13 presence_score for this module."
    )
    accreditation_readiness_score: float | None = Field(
        default=None, description="Stage 13 overall_score for this module."
    )
    outcome_coverage_percentage: float | None = Field(
        default=None, description="Stage 12 outcome coverage percentage for this module."
    )
    evidence_completeness_percentage: float | None = None
    risk_level: ReadinessRiskLevel
    is_high_risk: bool


# ---------------------------------------------------------------------------
# Findings summary (items 6/7)
# ---------------------------------------------------------------------------


class FindingsSummaryRead(BaseModel):
    """Aggregate counts of findings carried over from prior module audits."""

    total: int
    unresolved: int
    critical_total: int
    critical_unresolved: int
    high_unresolved: int


# ---------------------------------------------------------------------------
# Full programme review report
# ---------------------------------------------------------------------------


class ProgrammeReviewReport(BaseModel):
    """Full structured report for a completed programme review run.

    Returned by GET /programme-review-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    programme_id: uuid.UUID
    programme_code: str
    programme_name: str
    scope_type: str = Field(description="Entity scope assessed, e.g. 'programme'.")

    compliance_score: float = Field(description="Mean module compliance score (0-100, item 2).")
    accreditation_readiness_score: float = Field(
        description="Mean module accreditation readiness score (0-100, item 3)."
    )
    outcome_coverage_percentage: float = Field(
        description="Mean module outcome coverage percentage (0-100, item 4).", ge=0.0, le=100.0
    )
    evidence_completeness_percentage: float = Field(
        description="Mean module evidence-pack completeness percentage (0-100, item 8).",
        ge=0.0,
        le=100.0,
    )
    audit_status: AuditStatus
    risk_level: ReadinessRiskLevel = Field(
        description="Programme risk level derived from scores and module risk distribution (item 9)."
    )

    modules_total: int
    modules_with_data: int
    modules: list[ModuleReviewRead]
    high_risk_modules: list[str] = Field(description="Labels of modules flagged HIGH/CRITICAL risk (item 5).")

    findings_summary: FindingsSummaryRead

    gaps: list[str] = Field(description="Human-readable programme-level gaps identified.")
    recommendations: list[str] = Field(description="Deduplicated recommendations to address the gaps.")

    findings: list[ProgrammeFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class ProgrammeReviewRunBrief(BaseModel):
    """Lightweight run info for history lists."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    programme_id: uuid.UUID | None = None
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


class ProgrammeReviewRunRead(BaseModel):
    """Full audit run with findings list (no module breakdown; use /report for that)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    programme_id: uuid.UUID | None = None
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
    findings: list[ProgrammeFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class ProgrammeReviewTriggerResponse(BaseModel):
    """Returned immediately when a programme review audit is triggered."""

    run_id: uuid.UUID
    programme_id: uuid.UUID
    status: AuditRunStatus
    message: str
