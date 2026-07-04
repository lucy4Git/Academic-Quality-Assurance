"""Schemas for the Accreditation Readiness Audit endpoints (Stage 13).

Mirrors ``schemas/outcome_alignment.py`` (Stage 12) structurally -- the same
two-component score breakdown shape -- plus the sub-agent readiness
breakdown, findings summary, gaps, and recommendations specific to
accreditation readiness.
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


class ReadinessFindingRead(BaseModel):
    """An individual finding from an accreditation readiness run."""

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
# Sub-agent readiness breakdown (items 1-6)
# ---------------------------------------------------------------------------


class SubAgentReadinessRead(BaseModel):
    """Readiness breakdown for one of the six prior compliance agents."""

    group_id: str
    label: str
    agent_type: AgentType
    weight: int
    has_run: bool
    overall_score: float | None = Field(
        default=None,
        description="Latest overall score (0-100) for this agent, or null if not yet run.",
    )
    threshold: float = Field(description="Minimum acceptable score for accreditation readiness.")
    passed: bool = Field(description="True if has_run and overall_score >= threshold.")


# ---------------------------------------------------------------------------
# Findings summary (items 7/8)
# ---------------------------------------------------------------------------


class FindingsSummaryRead(BaseModel):
    """Aggregate counts of findings carried over from prior compliance audits."""

    total: int
    unresolved: int
    critical_total: int
    critical_unresolved: int
    high_unresolved: int


# ---------------------------------------------------------------------------
# Full accreditation readiness report
# ---------------------------------------------------------------------------


class AccreditationReadinessReport(BaseModel):
    """Full structured report for a completed accreditation readiness run.

    Returned by GET /accreditation-readiness-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    scope_type: str = Field(description="Entity scope assessed, e.g. 'module'.")

    presence_score: float = Field(description="Weighted sub-agent readiness checklist score (0-100).")
    quality_score: float = Field(description="Evidence-pack completeness + findings-resolution score (0-100).")
    overall_score: float = Field(description="Combined score: 60% presence + 40% quality (0-100).")
    audit_status: AuditStatus
    risk_level: ReadinessRiskLevel = Field(
        description="Accreditation readiness risk level derived from overall score and unresolved findings."
    )

    total_presence_weight: int
    achieved_presence_weight: float
    total_quality_weight: float
    achieved_quality_weight: float

    evidence_completeness_percentage: float = Field(
        description="Live accreditation evidence-pack completeness percentage (Stage 11 reuse).",
        ge=0.0,
        le=100.0,
    )

    sub_agent_readiness: list[SubAgentReadinessRead]
    findings_summary: FindingsSummaryRead

    gaps: list[str] = Field(description="Human-readable accreditation gaps identified for this scope.")
    recommendations: list[str] = Field(description="Deduplicated recommendations to address the gaps.")

    findings: list[ReadinessFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class AccreditationReadinessRunBrief(BaseModel):
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


class AccreditationReadinessRunRead(BaseModel):
    """Full audit run with findings list (no readiness breakdown; use /report for that)."""

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
    findings: list[ReadinessFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class AccreditationReadinessTriggerResponse(BaseModel):
    """Returned immediately when an accreditation readiness audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
