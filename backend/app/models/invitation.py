"""Invitation model — secure, single-use (or controlled-batch) institutional invitations.

Security invariants
-------------------
- The plaintext invitation token is NEVER stored here.
  Only the SHA-256 hex digest (`token_hash`) is persisted.
- The plaintext token is returned exactly once in the creation response
  and is then discarded by the service layer.
- `token_hash` has a unique index; brute-force enumeration is therefore
  equivalent to inverting SHA-256.
- Invitations are tenant-scoped: the inviter's institution_id is validated
  against the invitation's institution_id at creation time.
- Tenant administrators cannot create INSTITUTION_ADMIN invitations
  (requires SYSTEM_ADMIN authority).
- `expires_at` is enforced server-side; expired invitations are rejected
  even if their status is still PENDING.
- `max_uses` defaults to 1; setting it higher requires explicit intent
  from an authorised administrator and supports controlled batch onboarding.
- Every invitation lifecycle event is audit-logged.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class Invitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A pre-generated cryptographic invitation record.

    Role and institution are embedded here by the authorised inviter and
    cannot be altered by the invitee at registration time.
    """

    __tablename__ = "invitations"

    # SHA-256(plaintext_token) — only this is stored; token itself is one-shot
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    invitation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Role assigned when this invitation is consumed (UserRole string value)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Optional: restrict to a specific email address
    email_restriction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Optional: restrict to a specific email domain
    domain_restriction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Organisational scope (all nullable — invitation may be institution-wide)
    faculty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculties.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="SET NULL"),
        nullable=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
    )
    # JSON bag for extra permission metadata (external access scope, etc.)
    permission_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # InvitationStatus string value
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Whether the invitation requires email verification before activating
    requires_email_verification: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    institution: Mapped["Institution | None"] = relationship(
        "Institution", foreign_keys=[institution_id], lazy="selectin"
    )
    inviter: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by], lazy="selectin"
    )

    def is_valid(self) -> bool:
        """Return True only if this invitation can still be consumed."""
        from datetime import timezone
        now = datetime.now(tz=timezone.utc)
        return (
            self.status == "pending"
            and self.use_count < self.max_uses
            and self.expires_at > now
        )

    def __repr__(self) -> str:
        return (
            f"<Invitation type={self.invitation_type!r} "
            f"status={self.status!r} uses={self.use_count}/{self.max_uses}>"
        )
