"""BackgroundJobLog and AuditTriggerSchedule models.

M-E-00: Two new tables for the ARQ worker foundation.

BackgroundJobLog — persistent record of every ARQ job enqueued, its
status, tenant context, and outcome. Provides the dead-letter visibility
required by E0-OD-001 ('Do not claim ARQ provides a complete dead-letter
queue unless the implemented design explicitly creates one').

AuditTriggerSchedule — scheduled recurring audit triggers per module or
programme. Populated by coordinators; consumed by the ARQ worker cron.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BackgroundJobLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persistent record of every ARQ job enqueued."""

    __tablename__ = "background_job_logs"

    # ARQ's own job identifier (allows correlation with ARQ internals)
    arq_job_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Job type name matching the registered function
    job_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Tenant context — mandatory; NULL indicates a system-level job
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Lifecycle
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="enqueued", index=True
    )  # enqueued | running | completed | failed | dead_letter
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Timing
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Outcome
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditTriggerSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recurring scheduled audit triggers per module or programme."""

    __tablename__ = "audit_trigger_schedules"

    # Scope — exactly one of these must be non-null
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Which audit agent to trigger
    agent_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Cron expression (e.g. "0 2 * * 1" = every Monday at 02:00)
    cron_expression: Mapped[str] = mapped_column(String(128), nullable=False)

    # Tenant context
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_trigger_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
