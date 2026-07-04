"""Schemas for the Outcome Alignment Audit endpoints.

Mirrors ``schemas/evidence_audit.py`` (Stage 11) structurally -- the same
two-component score breakdown and per-document quality shapes -- plus the
outcome coverage breakdown (items 9/10) specific to outcome alignment.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentType,
    AlignmentRiskLevel,
    AuditRunStatus,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class OutcomeFindingRead(BaseModel):
    """An individual finding from an outcome alignment run."""

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


class DocumentAlignmentBreakdown(BaseModel):
    """Quality probe summary for a single document in an outcome run."""

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
# Outcome coverage (items 9/10)
# ---------------------------------------------------------------------------


class OutcomeCoverageRead(BaseModel):
    """Module-outcome -> assessment coverage breakdown."""

    programme_outcomes: list[str] = Field(description="Normalised programme outcome refs, e.g. ['po1', 'po2'].")
    module_outcomes: list[str] = Field(description="Normalised module outcome refs, e.g. ['mo1', 'mo2', 'mo3'].")
    covered_outcomes: list[str] = Field(description="Module outcomes referenced by at least one assessment task.")
    uncovered_outcomes: list[str] = Field(description="Module outcomes not referenced by any assessment task.")
    coverage_percentage: float = Field(
        description="0-100: percentage of module outcomes covered by at least one assessment task.",
        ge=0.0,
        le=100.0,
    )


# ---------------------------------------------------------------------------
# Presence checklist summary
# ---------------------------------------------------------------------------


class OutcomeGroupItem(BaseModel):
    """One required presence-checklist element and its status."""

    group_id: str
    label: str
    categories: list[FileCategory]
    severity: FindingSeverity
    weight: int
    present: bool


# ---------------------------------------------------------------------------
# Full outcome alignment report
# ---------------------------------------------------------------------------


class OutcomeAlignmentReport(BaseModel):
    """Full structured report for a completed outcome alignment run.

    Returned by GET /outcome-alignment-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    academic_year: str

    presence_score: float = Field(description="Weighted outcome-presence checklist score (0-100).")
    quality_score: float = Field(description="Weighted alignment/mapping quality probe score (0-100).")
    overall_score: float = Field(description="Combined score: 60% presence + 40% quality (0-100).")
    audit_status: AuditStatus
    risk_level: AlignmentRiskLevel = Field(
        description="Outcome alignment risk level derived from coverage and overall score."
    )

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_weight: float
    achieved_quality_weight: float

    outcome_groups: list[OutcomeGroupItem]
    document_alignment: list[DocumentAlignmentBreakdown]
    coverage: OutcomeCoverageRead

    findings: list[OutcomeFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class OutcomeAlignmentRunBrief(BaseModel):
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


class OutcomeAlignmentRunRead(BaseModel):
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
    findings: list[OutcomeFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class OutcomeAlignmentTriggerResponse(BaseModel):
    """Returned immediately when an outcome alignment audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
