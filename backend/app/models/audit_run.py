"""AuditRun ORM model.

An AuditRun represents one execution of the Module Folder Audit Agent against a
specific module.  Multiple runs are created over time to track compliance
improvements — every trigger creates a new row rather than overwriting the
previous one, giving full audit history.

Relationships
-------------
  AuditRun ←── many ──── AuditFinding   (one run produces 0-N findings)
  AuditRun ────── Module                (the audited module)
  AuditRun ────── Institution           (denormalised for tenant queries)
  AuditRun ────── User                  (who triggered the run)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AgentType, AuditRunStatus, AuditStatus

if TYPE_CHECKING:
    from app.models.audit_finding import AuditFinding
    from app.models.institution import Institution
    from app.models.module import Module
    from app.models.programme import Programme
    from app.models.user import User


class AuditRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One execution of the Module Folder Audit Agent."""

    __tablename__ = "audit_runs"

    # ------------------------------------------------------------------
    # Agent discriminator
    # ------------------------------------------------------------------

    agent_type: Mapped[AgentType] = mapped_column(
        String(40),
        nullable=False,
        default=AgentType.MODULE_FOLDER_AUDIT,
        index=True,
        comment="Which AI audit agent produced this run.",
    )

    # ------------------------------------------------------------------
    # Tenant + ownership
    # ------------------------------------------------------------------

    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Set for module-scoped agents. NULL for programme/faculty/institution-scoped runs.",
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Set for programme-scoped agents (e.g. Programme Review). NULL for module-scoped runs.",
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    run_status: Mapped[AuditRunStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AuditRunStatus.PENDING,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Compliance result
    # ------------------------------------------------------------------

    compliance_score: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Weighted compliance score 0.0–100.0.",
    )
    audit_status: Mapped[AuditStatus | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    total_required: Mapped[int | None] = mapped_column(Integer, nullable=True)
    documents_present: Mapped[int | None] = mapped_column(Integer, nullable=True)
    documents_missing: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    module: Mapped[Module | None] = relationship(
        "Module", foreign_keys=[module_id], lazy="raise"
    )
    programme: Mapped[Programme | None] = relationship(
        "Programme", foreign_keys=[programme_id], lazy="raise"
    )
    institution: Mapped[Institution] = relationship(
        "Institution", foreign_keys=[institution_id], lazy="raise"
    )
    triggered_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[triggered_by_id], lazy="raise"
    )
    findings: Mapped[list[AuditFinding]] = relationship(
        "AuditFinding",
        back_populates="audit_run",
        cascade="all, delete-orphan",
        order_by="AuditFinding.severity",
        lazy="raise",
    )
