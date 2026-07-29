"""Secure single-use activation / password-reset token.

Tokens are NEVER stored in plaintext. The raw token is sent to the user
via email or link; only its SHA-256 digest is persisted here.

Lifecycle
---------
created (unused)
  → used_at IS NOT NULL   — consumed; subsequent attempts return 403
  → invalidated_at IS NOT NULL — superseded (resend issued new token)
  → expires_at < now()    — expired; user must request resend
  → failed_attempts ≥ 5   — brute-force lockout
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserActivationToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_activation_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hex digest of the raw 32-byte token sent to the user.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True, unique=True)

    # 'activation' (post-approval account setup) | 'password_reset'
    purpose: Mapped[str] = mapped_column(String(20), nullable=False, default="activation")

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Set when successfully consumed.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Set when a newer token supersedes this one (resend).
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Incremented on each failed attempt; locked at MAX_ATTEMPTS.
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # UUID of the admin user who triggered approval and generated this token.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[user_id],
        back_populates="activation_tokens",
    )

    def is_valid(self) -> bool:
        """True only when the token can still be used."""
        from datetime import timezone
        now = datetime.now(tz=timezone.utc)
        return (
            self.used_at is None
            and self.invalidated_at is None
            and self.expires_at > now
            and self.failed_attempts < 5
        )
