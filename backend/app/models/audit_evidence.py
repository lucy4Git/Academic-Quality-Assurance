"""AuditEvidence — links an uploaded file to an audit checklist item.

Rather than duplicating the full file-storage system, AuditEvidence is a
join record that attaches an existing File row (which already handles
storage, versioning, and checksums) to a specific AuditChecklistItem.
The same file can be linked to multiple checklist items via separate
AuditEvidence rows.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit_checklist_item_ref import AuditChecklistItem  # noqa: F401
    from app.models.institution import Institution
    from app.models.module import Module
    from app.models.module_audit import ModuleAudit
    from app.models.user import User


class AuditEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata record for a file uploaded as evidence against an audit item.

    The actual bytes are stored on disk (LocalStorageBackend) and referenced
    via ``stored_path``.  This model intentionally avoids a FK to the File
    table so evidence uploads are self-contained and not affected by
    soft-deletes on the general file library.
    """

    __tablename__ = "audit_evidence"

    # ── Scope (denormalized for fast tenant queries) ──────────────────────
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("module_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checklist_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_checklist_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="NULL = audit-level evidence not tied to a specific checklist item",
    )
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── File metadata ─────────────────────────────────────────────────────
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(
        String(1000), nullable=False,
        comment="Path relative to the configured STORAGE_LOCAL_PATH root",
    )
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    evidence_category: Mapped[str] = mapped_column(
        String(80), nullable=False, default="general",
        comment="e.g. 'marking_guide', 'attendance_register', 'general'",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    institution: Mapped["Institution"] = relationship(
        "Institution", foreign_keys=[institution_id], lazy="raise"
    )
    module: Mapped["Module"] = relationship(
        "Module", foreign_keys=[module_id], lazy="raise"
    )
    audit: Mapped["ModuleAudit"] = relationship(
        "ModuleAudit", foreign_keys=[audit_id], lazy="raise"
    )
    uploaded_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[uploaded_by_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<AuditEvidence {self.original_filename!r} audit={self.audit_id}>"
