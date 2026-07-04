"""AuditFinding ORM model.

One AuditFinding represents a single issue or observation raised during an
AuditRun.  Findings are immutable once created — resolutions are tracked via
the ``is_resolved`` flag rather than deletion, preserving the full audit trail.

Finding types
-------------
  MISSING_DOCUMENT   — a required category has no uploaded file.
  MISCLASSIFIED      — a file's category may be wrong (machine suggestion differs).
  QUALITY_ISSUE      — an uploaded document appears to have quality problems.
  RECOMMENDATION     — an improvement suggestion (not a compliance failure).
  INFO               — informational note (e.g. machine-classification suggestion).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FileCategory, FindingSeverity, FindingType

if TYPE_CHECKING:
    from app.models.audit_run import AuditRun
    from app.models.file import File


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
    # Resolution tracking
    # ------------------------------------------------------------------

    is_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    resolved_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    audit_run: Mapped[AuditRun] = relationship(
        "AuditRun", back_populates="findings", lazy="raise"
    )
    file: Mapped[File | None] = relationship(
        "File", foreign_keys=[file_id], lazy="raise"
    )
