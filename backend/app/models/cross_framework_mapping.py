"""CrossFrameworkMapping ORM model — Phase C."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CrossFrameworkRelation


class CrossFrameworkMapping(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Maps a criterion or standard in one framework version to another.

    AI may propose mappings (human_verified=FALSE) but cannot mark two
    criteria as legally equivalent without human verification.

    Covers mappings at standard level OR criterion level:
    - Standard-to-standard: standard_a_id + standard_b_id set, criteria NULL
    - Criterion-to-criterion: criterion_a_id + criterion_b_id set
    """

    __tablename__ = "cross_framework_mappings"

    # Source (framework A)
    framework_version_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    standard_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="CASCADE"),
        nullable=True,
    )
    criterion_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Target (framework B)
    framework_version_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    standard_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="CASCADE"),
        nullable=True,
    )
    criterion_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="CASCADE"),
        nullable=True,
    )

    relation: Mapped[CrossFrameworkRelation] = mapped_column(
        String(30), nullable=False, index=True
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Human verification required before EQUIVALENT mappings are used for deduplication
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

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
