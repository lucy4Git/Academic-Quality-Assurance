"""FrameworkStandard ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.framework_criterion import FrameworkCriterion
    from app.models.framework_version import FrameworkVersion


class FrameworkStandard(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A standard within a framework version.

    Standards can be nested (parent_standard_id) to support hierarchical
    frameworks (e.g., CHE: Area → Standard → Criterion).
    """

    __tablename__ = "framework_standards"

    framework_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_standard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    citation_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)

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
    framework_version: Mapped[FrameworkVersion] = relationship(
        "FrameworkVersion", back_populates="standards"
    )
    criteria: Mapped[list[FrameworkCriterion]] = relationship(
        "FrameworkCriterion", back_populates="standard", lazy="select"
    )
    children: Mapped[list[FrameworkStandard]] = relationship(
        "FrameworkStandard",
        foreign_keys=[parent_standard_id],
        lazy="select",
    )
