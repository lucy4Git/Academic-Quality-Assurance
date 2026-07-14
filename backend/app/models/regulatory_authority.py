"""RegulatoryAuthority ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AuthorityStatus, AuthorityType

if TYPE_CHECKING:
    from app.models.quality_framework import QualityFramework


class RegulatoryAuthority(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A national regulator, quality council, professional body, or internal authority.

    Global (shared) authorities: institution_id = NULL, is_external = TRUE.
    Institution-defined authorities: institution_id set, is_internal = TRUE.
    """

    __tablename__ = "regulatory_authorities"

    # Optional scoping — NULL for shared/global authorities
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(40), nullable=True)
    authority_type: Mapped[AuthorityType] = mapped_column(String(40), nullable=False, index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(60), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_information: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_external: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[AuthorityStatus] = mapped_column(
        String(20), default=AuthorityStatus.ACTIVE, nullable=False
    )

    # Audit trail — who created/last-updated
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    frameworks: Mapped[list[QualityFramework]] = relationship(
        "QualityFramework", back_populates="authority", lazy="select"
    )
