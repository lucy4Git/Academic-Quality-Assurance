"""FrameworkAssessmentRun and CriterionAssessmentResult ORM models — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ApplicabilityTargetType,
    EvaluationMethod,
    FindingSeverity,
    FrameworkAssessmentStatus,
    RegulatoryRisk,
)


class FrameworkAssessmentRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An assessment of a specific entity against a specific framework version.

    Scores are stored at three independent levels so mandatory failures
    cannot be hidden inside an averaged composite score:
      - mandatory_compliance_score: 0 if ANY mandatory criterion is unmet
      - evidence_coverage_score: fraction of evidence requirements satisfied
      - quality_score: average quality of provided evidence
    """

    __tablename__ = "framework_assessment_runs"

    # Tenant scoping
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    framework_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # What is being assessed
    target_entity_type: Mapped[ApplicabilityTargetType] = mapped_column(
        String(30), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    assessment_scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assessment_period: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[FrameworkAssessmentStatus] = mapped_column(
        String(30), default=FrameworkAssessmentStatus.QUEUED, nullable=False, index=True
    )
    started_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scores (all 0–100, stored separately — never averaged before surfacing)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mandatory_compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_coverage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    risk_level: Mapped[RegulatoryRisk | None] = mapped_column(String(20), nullable=True)
    readiness_status: Mapped[str | None] = mapped_column(String(30), nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Counts for quick display
    criteria_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criteria_met: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criteria_unmet: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mandatory_failures: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    criterion_results: Mapped[list[CriterionAssessmentResult]] = relationship(
        "CriterionAssessmentResult",
        back_populates="assessment_run",
        lazy="select",
        cascade="all, delete-orphan",
    )


class CriterionAssessmentResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Result of evaluating a single criterion in a framework assessment.

    Stores the full evidence trace so the assessment is auditable and
    explainable. Deterministic, semantic, and human-review results are
    stored separately and never silently merged.
    """

    __tablename__ = "criterion_assessment_results"

    assessment_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_assessment_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    evidence_requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Evidence trace
    evidence_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_missing: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of UUIDs

    # Results by evaluation type (kept separate)
    deterministic_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    semantic_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    human_review_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Final result
    is_met: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    severity: Mapped[FindingSeverity | None] = mapped_column(String(20), nullable=True)
    evaluation_method: Mapped[EvaluationMethod | None] = mapped_column(String(30), nullable=True)
    citation_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Finding linkage (populated by regulatory_findings_service on gap promotion)
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_findings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    assessment_run: Mapped[FrameworkAssessmentRun] = relationship(
        "FrameworkAssessmentRun", back_populates="criterion_results"
    )
