"""Module Folder Audit ORM models.

A ModuleAudit is a manual QA checklist performed by a QA Officer or Dean
against a specific module's folder.  Each audit contains a fixed set of
AuditChecklistItems (one per QA criterion).

Distinct from the AI-driven AuditRun model (which is used by automated
agents) — this model captures human-conducted quality assurance reviews.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AuditPriority, ChecklistItemStatus, ModuleAuditStatus, WorkflowStatus

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.institution import Institution
    from app.models.module import Module
    from app.models.programme import Programme
    from app.models.user import User


# ---------------------------------------------------------------------------
# Checklist item keys — one row per key per audit
# ---------------------------------------------------------------------------

CHECKLIST_ITEMS: list[tuple[str, str]] = [
    ("course_outcomes",      "Course/Module Outcomes Present"),
    ("course_content",       "Course Content Present"),
    ("assessment_plan",      "Assessment Plan Present"),
    ("internal_moderation",  "Internal Moderation Report Present"),
    ("assessment_memo",      "Assessment Memo Present"),
    ("attendance_evidence",  "Attendance Evidence Present"),
    ("learner_evidence",     "Learner Evidence Present"),
    ("marking_guide",        "Marking Guide/Rubric Present"),
    ("lecturer_evidence",    "Lecturer Evidence Present"),
    ("approval_signoff",     "Approval/Sign-off Present"),
]


class ModuleAudit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One manual QA folder audit against a module."""

    __tablename__ = "module_audits"

    # ── Scope ──────────────────────────────────────────────────────────────
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    programme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Auditor ────────────────────────────────────────────────────────────
    auditor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Audit metadata ─────────────────────────────────────────────────────
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Computed compliance fields (recalculated on every save) ───────────
    status: Mapped[ModuleAuditStatus] = mapped_column(
        Enum(ModuleAuditStatus, name="module_audit_status", native_enum=True),
        nullable=False,
        default=ModuleAuditStatus.DRAFT,
        index=True,
    )
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compliant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_applicable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compliance_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Workflow fields ────────────────────────────────────────────────────────
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflow_status", native_enum=True),
        nullable=False,
        default=WorkflowStatus.DRAFT,
        index=True,
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[AuditPriority | None] = mapped_column(
        Enum(AuditPriority, name="audit_priority", native_enum=True),
        nullable=True,
    )
    assignment_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    module: Mapped[Module] = relationship("Module", foreign_keys=[module_id], lazy="raise")
    programme: Mapped[Programme] = relationship("Programme", foreign_keys=[programme_id], lazy="raise")
    department: Mapped[Department] = relationship("Department", foreign_keys=[department_id], lazy="raise")
    faculty: Mapped[Faculty] = relationship("Faculty", foreign_keys=[faculty_id], lazy="raise")
    institution: Mapped[Institution] = relationship("Institution", foreign_keys=[institution_id], lazy="raise")
    auditor: Mapped[User | None] = relationship("User", foreign_keys=[auditor_id], lazy="raise")
    assigned_to: Mapped[User | None] = relationship("User", foreign_keys=[assigned_to_id], lazy="raise")
    assigned_by: Mapped[User | None] = relationship("User", foreign_keys=[assigned_by_id], lazy="raise")
    checklist_items: Mapped[list[AuditChecklistItem]] = relationship(
        "AuditChecklistItem",
        back_populates="audit",
        cascade="all, delete-orphan",
        order_by="AuditChecklistItem.item_key",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<ModuleAudit module={self.module_id} status={self.status.value}>"


class AuditChecklistItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One checklist criterion within a ModuleAudit."""

    __tablename__ = "audit_checklist_items"
    __table_args__ = (
        UniqueConstraint("audit_id", "item_key", name="uq_checklist_audit_key"),
    )

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("module_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_key: Mapped[str] = mapped_column(String(60), nullable=False)
    item_label: Mapped[str] = mapped_column(String(120), nullable=False)

    status: Mapped[ChecklistItemStatus] = mapped_column(
        Enum(ChecklistItemStatus, name="checklist_item_status", native_enum=True),
        nullable=False,
        default=ChecklistItemStatus.MISSING,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    audit: Mapped[ModuleAudit] = relationship(
        "ModuleAudit", back_populates="checklist_items", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<AuditChecklistItem key={self.item_key!r} status={self.status.value}>"
