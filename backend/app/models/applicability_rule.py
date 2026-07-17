"""ApplicabilityRule ORM model — Phase C."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ApplicabilityTargetType

if TYPE_CHECKING:
    from app.models.framework_version import FrameworkVersion


class ApplicabilityRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Declarative rule determining which entities a framework version applies to.

    Rules are stored as JSON condition trees (safe, no code execution).
    The applicability service evaluates them against entity attributes.

    Example rule_conditions (stored as JSON text):
    {
      "operator": "AND",
      "conditions": [
        {"field": "programme.qualification_type", "op": "eq", "value": "B.Eng"},
        {"field": "institution.country", "op": "eq", "value": "ZA"}
      ]
    }

    is_inclusion_rule = TRUE  → entity IS included when conditions match
    is_exclusion_rule = TRUE  → entity IS EXCLUDED when conditions match
    Both cannot be TRUE simultaneously.
    """

    __tablename__ = "applicability_rules"

    framework_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optional narrow scoping to a standard or criterion within the version
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="SET NULL"),
        nullable=True,
    )
    criterion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="SET NULL"),
        nullable=True,
    )

    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_entity_type: Mapped[ApplicabilityTargetType] = mapped_column(
        String(30), nullable=False, index=True
    )

    # Safe declarative JSON condition tree (TEXT column)
    rule_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    is_inclusion_rule: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_exclusion_rule: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    framework_version: Mapped[FrameworkVersion] = relationship(
        "FrameworkVersion", back_populates="applicability_rules"
    )
