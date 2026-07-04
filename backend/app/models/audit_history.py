"""AuditHistory — immutable timeline events for a ModuleAudit.

Every significant state change appends a new row; rows are never updated
or deleted. This gives QA Officers a full, auditable trail of what happened
to an audit and when.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.module_audit import ModuleAudit
    from app.models.user import User


class AuditHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One timeline event for a module folder audit."""

    __tablename__ = "audit_history"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("module_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Event type — one of the EVENT_* constants below
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)

    # Human-readable description rendered in the timeline
    summary: Mapped[str] = mapped_column(String(500), nullable=False)

    # Optional JSON-serialisable diff stored as text
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    audit: Mapped["ModuleAudit"] = relationship(
        "ModuleAudit", foreign_keys=[audit_id], lazy="raise"
    )
    actor: Mapped["User | None"] = relationship(
        "User", foreign_keys=[actor_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<AuditHistory event={self.event_type!r} audit={self.audit_id}>"


# ---------------------------------------------------------------------------
# Event type constants (stored as strings for readability in the DB)
# ---------------------------------------------------------------------------
EVENT_AUDIT_CREATED       = "audit_created"
EVENT_CHECKLIST_UPDATED   = "checklist_updated"
EVENT_EVIDENCE_UPLOADED   = "evidence_uploaded"
EVENT_EVIDENCE_DELETED    = "evidence_deleted"
EVENT_STATUS_CHANGED      = "status_changed"
EVENT_COMPLIANCE_CHANGED  = "compliance_changed"
EVENT_NOTES_UPDATED       = "notes_updated"
EVENT_WORKFLOW_CHANGED    = "workflow_status_changed"
EVENT_COMMENT_ADDED       = "comment_added"
