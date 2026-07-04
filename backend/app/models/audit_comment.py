"""AuditComment — threaded comments on a ModuleAudit."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.module_audit import ModuleAudit
    from app.models.user import User


class AuditComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A comment posted on a module folder audit."""

    __tablename__ = "audit_comments"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("module_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    audit: Mapped[ModuleAudit] = relationship(
        "ModuleAudit", foreign_keys=[audit_id], lazy="raise"
    )
    author: Mapped[User | None] = relationship(
        "User", foreign_keys=[author_id], lazy="raise"
    )
    institution: Mapped[Institution] = relationship(
        "Institution", foreign_keys=[institution_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<AuditComment audit={self.audit_id} author={self.author_id}>"
