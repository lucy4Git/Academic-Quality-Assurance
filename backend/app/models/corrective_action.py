"""CorrectiveAction and CorrectiveActionHistory models.

M-E-01: Two new tables for the corrective action workflow.
M-E-07: primary_corrective_action_id FK added to audit_findings (in migration).

CorrectiveAction — tracks a specific action required to resolve one or more
audit findings. Supports assignment, due dates, approval gates, and closure.

CorrectiveActionHistory — immutable audit trail for every state change.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CorrectiveAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific action required to address one or more audit findings."""

    __tablename__ = "corrective_actions"

    # --- Tenant scope ---
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Title and description ---
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Root finding this action addresses (optional — may address multiple) ---
    primary_finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Assignment ---
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Lifecycle ---
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open", index=True
    )  # open | in_progress | pending_approval | approved | closed | rejected

    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default="medium"
    )  # low | medium | high | critical

    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Closure ---
    closure_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class CorrectiveActionHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail for every CorrectiveAction state change."""

    __tablename__ = "corrective_action_history"

    corrective_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("corrective_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
