"""FrameworkCriterion ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import EvaluationMethod

if TYPE_CHECKING:
    from app.models.evidence_requirement import EvidenceRequirement
    from app.models.framework_standard import FrameworkStandard


class FrameworkCriterion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific, evaluable criterion within a standard.

    Criteria are the smallest evaluatable units of a framework.
    Each criterion specifies how it must be evaluated (evaluation_method)
    and whether it requires human review.
    """

    __tablename__ = "framework_criteria"

    standard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_criterion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="CASCADE"),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)

    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    evaluation_method: Mapped[EvaluationMethod] = mapped_column(
        String(30), default=EvaluationMethod.DOCUMENT_PRESENCE, nullable=False
    )
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
    standard: Mapped[FrameworkStandard] = relationship(
        "FrameworkStandard", back_populates="criteria"
    )
    evidence_requirements: Mapped[list[EvidenceRequirement]] = relationship(
        "EvidenceRequirement", back_populates="criterion", lazy="select"
    )
    children: Mapped[list[FrameworkCriterion]] = relationship(
        "FrameworkCriterion",
        foreign_keys=[parent_criterion_id],
        lazy="select",
    )
