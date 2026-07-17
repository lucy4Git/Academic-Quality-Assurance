"""EvidenceRequirement ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import EvidenceType, FileCategory

if TYPE_CHECKING:
    from app.models.framework_criterion import FrameworkCriterion


class EvidenceRequirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific piece of evidence required by a framework criterion.

    Links framework criteria to the AQAA document/evidence system.
    `document_category` maps to the existing FileCategory enum so
    existing uploaded files can be matched automatically.
    """

    __tablename__ = "evidence_requirements"

    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence_type: Mapped[EvidenceType] = mapped_column(
        String(30), default=EvidenceType.DOCUMENT, nullable=False
    )
    # Maps to FileCategory enum for automatic document matching
    document_category: Mapped[FileCategory | None] = mapped_column(
        String(40), nullable=True, index=True
    )

    minimum_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    maximum_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    requires_signature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_date: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_version: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quality_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)

    # JSON-serialised rule expression (safe declarative format, no code execution)
    validation_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Comma-separated accepted file extensions, e.g. ".pdf,.docx"
    accepted_file_types: Mapped[str | None] = mapped_column(String(200), nullable=True)

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
    criterion: Mapped[FrameworkCriterion] = relationship(
        "FrameworkCriterion", back_populates="evidence_requirements"
    )
