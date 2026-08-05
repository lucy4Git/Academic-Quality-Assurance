"""InstitutionDomain model — maps verified email domains to institutions.

Purpose
-------
When a student registers with an institutional email (e.g. s12345@tut.ac.za),
the backend extracts the domain (`tut.ac.za`), looks it up in this table, and
— if a matching active record is found — automatically links the student to the
correct institution without any browser-submitted institution_id.

Security invariants
-------------------
- Only a SYSTEM_ADMIN may create, update, or delete domain records.
- No public endpoint exposes domain-to-institution mapping information.
- Domain matching is always performed server-side; browser input is ignored.
- `auto_assign_student=True` is the only automatic role a domain grants;
  it never assigns a privileged staff role.
- Institutions may disable automatic mapping by setting `auto_assign_student=False`.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class InstitutionDomain(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A verified email domain associated with an institution.

    `domain` is stored in normalised lowercase form (no leading `@`).
    The unique constraint prevents the same domain from being claimed by
    multiple institutions.
    """

    __tablename__ = "institution_domains"
    __table_args__ = (
        UniqueConstraint("domain", name="uq_institution_domain_domain"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        # normalised by the service layer — lowercase, no @ prefix
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # When True, a registrant with a matching verified email is automatically
    # assigned role=student and linked to this institution after email verification.
    auto_assign_student: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    institution: Mapped["Institution"] = relationship(back_populates="domains")
    creator: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<InstitutionDomain domain={self.domain!r} institution_id={self.institution_id}>"
