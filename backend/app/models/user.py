"""User model — platform identity and role, scoped to an institution.

Authentication concerns (password hashing, token issuance, login flows) are
intentionally NOT implemented here; they belong to `security.py` /
`services/auth_service.py` in the next stage. This model only defines the
persisted shape of a user.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.invitation import Invitation
    from app.models.user_activation_token import UserActivationToken
    from app.models.user_workspace_module import UserWorkspaceModule


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A platform user (lecturer, coordinator, dean, QA officer, admin, ...).

    `institution_id` is nullable to accommodate system administrators who are
    not bound to a single tenant; all other roles are expected to carry one.

    Email verification + approval flow
    -----------------------------------
    Public registrations land here with is_active=False, is_verified=False,
    approval_status='pending'.  They become active only after:
      1. Email verification (is_verified=True)
      2. Admin/system admin approval (is_active=True, approval_status='approved')
    """

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        default=UserRole.LECTURER,
    )
    # For GENERIC_USER role only: determines UX/workspace (quality_assurance_officer|lecturer).
    # For institutional users: null. Never used for authorization.
    persona: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Email verification ---
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verification_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Admin approval ---
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="approved"
    )
    role_requested: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_for_access: Mapped[str | None] = mapped_column(String(500), nullable=True)
    institution_name_requested: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Onboarding preferences (generic users only) ---
    # JSON array of primary QA tasks (e.g., ["review_module", "find_missing_documents"])
    qa_interests: Mapped[list[str] | None] = mapped_column(
        JSON(), nullable=True, default=None
    )
    # JSON array of evidence types (e.g., ["module_guides", "assessments"])
    evidence_types: Mapped[list[str] | None] = mapped_column(
        JSON(), nullable=True, default=None
    )

    # FK to the invitation used to register (null for self-service students)
    invitation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invitations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    institution: Mapped["Institution | None"] = relationship(back_populates="users")
    invitation: Mapped["Invitation | None"] = relationship(
        "Invitation", foreign_keys=[invitation_id], lazy="selectin"
    )
    activation_tokens: Mapped[list["UserActivationToken"]] = relationship(
        "UserActivationToken",
        foreign_keys="UserActivationToken.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    workspace_modules: Mapped[list["UserWorkspaceModule"]] = relationship(
        "UserWorkspaceModule",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        role_val = self.role.value if isinstance(self.role, UserRole) else self.role
        return f"<User email={self.email!r} role={role_val}>"
