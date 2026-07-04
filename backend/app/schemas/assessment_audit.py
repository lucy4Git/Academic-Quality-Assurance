"""Schemas for the Assessment Compliance Audit endpoints.

These schemas are specific to the Assessment Compliance Agent.  They extend
the shared audit schemas from ``schemas/audit.py`` and add the two-component
scoring breakdown and per-document quality information that are unique to this
agent.
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
)


# ---------------------------------------------------------------------------
# Finding (re-uses shared shape, reproduced here for self-contained import)
# ---------------------------------------------------------------------------


class AssessmentFindingRead(BaseModel):
    """An individual finding from an assessment compliance run."""

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
# Document quality breakdown (per-document probe result)
# ---------------------------------------------------------------------------


class ProbeResultRead(BaseModel):
    """Pass/fail outcome for one TextProbe against one document."""

    probe_id: str
    label: str
    passed: bool
    severity: FindingSeverity
    weight: float


class DocumentQualityBreakdown(BaseModel):
    """Quality probe summary for a single document in an assessment run."""

    file_id: uuid.UUID
    filename: str
    category: FileCategory
    has_extraction: bool
    probes_run: int
    probes_passed: int
    quality_score: float = Field(
        description="0–100: percentage of weighted probe weight passed.",
        ge=0.0,
        le=100.0,
    )
    probe_results: list[ProbeResultRead]


# ---------------------------------------------------------------------------
# Presence checklist summary
# ---------------------------------------------------------------------------


class AssessmentDocumentItem(BaseModel):
    """One required assessment document and its compliance status."""

    category: FileCategory
    label: str
    severity: FindingSeverity
    weight: int
    present: bool


# ---------------------------------------------------------------------------
# Full assessment compliance report
# ---------------------------------------------------------------------------


class AssessmentComplianceReport(BaseModel):
    """Full structured report for a completed assessment compliance run.

    Returned by GET /assessment-audits/{run_id}/report.
    """

    run_id: uuid.UUID
    module_id: uuid.UUID
    module_code: str
    academic_year: str

    # Two-component scoring.
    presence_score: float = Field(description="Weighted document presence score (0–100).")
    quality_score: float  = Field(description="Weighted content quality probe score (0–100).")
    overall_score: float  = Field(description="Combined score: 60% presence + 40% quality (0–100).")
    audit_status: AuditStatus

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_probes: int
    passed_quality_probes: int

    # Document checklists.
    documents_present: list[AssessmentDocumentItem]
    documents_missing: list[AssessmentDocumentItem]

    # Per-document content quality.
    document_quality: list[DocumentQualityBreakdown]

    # Flat findings list.
    findings: list[AssessmentFindingRead]
    finding_counts: dict[str, int] = Field(
        description="Count of findings per severity: critical, high, medium, low, info."
    )

    summary: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Audit run schemas
# ---------------------------------------------------------------------------


class AssessmentRunBrief(BaseModel):
    """Lightweight run info for history lists."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    agent_type: AgentType
    run_status: AuditRunStatus
    audit_status: AuditStatus | None = None
    presence_score: float | None = Field(default=None, alias="compliance_score")
    overall_score: float | None = Field(default=None, alias="compliance_score")
    documents_present: int | None = None
    documents_missing: int | None = None
    triggered_by_id: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AssessmentRunRead(BaseModel):
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
    findings: list[AssessmentFindingRead] = []


# ---------------------------------------------------------------------------
# Trigger response
# ---------------------------------------------------------------------------


class AssessmentTriggerResponse(BaseModel):
    """Returned immediately when an assessment audit is triggered."""

    run_id: uuid.UUID
    module_id: uuid.UUID
    status: AuditRunStatus
    message: str
