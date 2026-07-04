"""Notification — in-app notifications for AQAA users."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import NotificationType

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.module_audit import ModuleAudit
    from app.models.user import User


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An in-app notification delivered to a specific user."""

    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", native_enum=True),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("module_audits.id", ondelete="SET NULL"),
        nullable=True,
    )

    recipient: Mapped[User] = relationship(
        "User", foreign_keys=[recipient_id], lazy="raise"
    )
    institution: Mapped[Institution] = relationship(
        "Institution", foreign_keys=[institution_id], lazy="raise"
    )
    audit: Mapped[ModuleAudit | None] = relationship(
        "ModuleAudit", foreign_keys=[audit_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Notification type={self.notification_type} recipient={self.recipient_id}>"
