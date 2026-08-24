"""AuditFinding ORM model and FindingStatusHistory audit trail."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FileCategory, FindingSeverity, FindingStatus, FindingType, RegulatoryRisk

if TYPE_CHECKING:
    from app.models.audit_run import AuditRun
    from app.models.file import File
    from app.models.user import User


class AuditFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single finding produced by an audit run."""

    __tablename__ = "audit_findings"

    # ------------------------------------------------------------------
    # Parent run
    # ------------------------------------------------------------------

    audit_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Finding classification
    # ------------------------------------------------------------------

    finding_type: Mapped[FindingType] = mapped_column(
        String(30), nullable=False, index=True
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        String(20), nullable=False, index=True
    )

    # Which document category this finding concerns (NULL for non-document findings).
    document_category: Mapped[FileCategory | None] = mapped_column(
        String(40), nullable=True, index=True
    )

    # Optional reference to a specific file (for MISCLASSIFIED / QUALITY_ISSUE).
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    # ------------------------------------------------------------------
    # Lifecycle status (10-state machine)
    # ------------------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FindingStatus.OPEN,
        index=True,
    )

    # Who created/discovered this finding (audit agent or manual entry).
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional user assigned to action this finding.
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Due date for corrective action (ISO date stored as String for simplicity).
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # ------------------------------------------------------------------
    # Legacy resolution tracking (kept for backwards compat)
    # is_resolved is now derived: status == FindingStatus.RESOLVED
    # ------------------------------------------------------------------

    is_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    resolved_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Phase C — Regulatory citations (all nullable; not set by legacy agents)
    # ------------------------------------------------------------------

    regulatory_authority_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    framework_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="SET NULL"),
        nullable=True,
    )
    criterion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    citation_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    regulatory_risk: Mapped[RegulatoryRisk | None] = mapped_column(String(20), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    audit_run: Mapped[AuditRun] = relationship(
        "AuditRun", back_populates="findings", lazy="raise"
    )
    file: Mapped[File | None] = relationship(
        "File", foreign_keys=[file_id], lazy="raise"
    )
    assigned_to: Mapped[User | None] = relationship(
        "User", foreign_keys=[assigned_to_id], lazy="raise"
    )
    status_history: Mapped[list[FindingStatusHistory]] = relationship(
        "FindingStatusHistory",
        back_populates="finding",
        lazy="raise",
        order_by="FindingStatusHistory.created_at",
    )


class FindingStatusHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable audit trail of every status transition on a finding."""

    __tablename__ = "finding_status_history"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    finding: Mapped[AuditFinding] = relationship(
        "AuditFinding", back_populates="status_history", lazy="raise"
    )
    changed_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[changed_by_id], lazy="raise"
    )
