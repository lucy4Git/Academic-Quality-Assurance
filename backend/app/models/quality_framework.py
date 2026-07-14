"""QualityFramework ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FrameworkScope, FrameworkType

if TYPE_CHECKING:
    from app.models.framework_version import FrameworkVersion
    from app.models.regulatory_authority import RegulatoryAuthority


class QualityFramework(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A regulatory, quality, or accreditation framework.

    Can be a national standard (institution_id=NULL), or an institution-specific
    policy (institution_id set).
    """

    __tablename__ = "quality_frameworks"

    authority_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_authorities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # NULL → shared/global framework; set → institution-specific
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    framework_type: Mapped[FrameworkType] = mapped_column(String(50), nullable=False, index=True)
    scope: Mapped[FrameworkScope] = mapped_column(String(30), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    authority: Mapped[RegulatoryAuthority] = relationship(
        "RegulatoryAuthority", back_populates="frameworks"
    )
    versions: Mapped[list[FrameworkVersion]] = relationship(
        "FrameworkVersion", back_populates="framework", lazy="select"
    )
