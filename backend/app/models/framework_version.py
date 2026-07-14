"""FrameworkVersion ORM model — Phase C."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SourceStatus, VersionStatus

if TYPE_CHECKING:
    from app.models.applicability_rule import ApplicabilityRule
    from app.models.framework_standard import FrameworkStandard
    from app.models.quality_framework import QualityFramework


class FrameworkVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific version of a quality framework.

    All assessments reference a specific version, not the framework itself.
    Only one version can be ACTIVE per framework at any time (enforced in service).
    """

    __tablename__ = "framework_versions"

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quality_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[str] = mapped_column(String(30), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[VersionStatus] = mapped_column(
        String(20), default=VersionStatus.DRAFT, nullable=False, index=True
    )

    # FK to the version this one supersedes (nullable)
    supersedes_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Source document reference
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_status: Mapped[SourceStatus] = mapped_column(
        String(40), default=SourceStatus.TEST_FIXTURE, nullable=False
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

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
    framework: Mapped[QualityFramework] = relationship(
        "QualityFramework", back_populates="versions"
    )
    standards: Mapped[list[FrameworkStandard]] = relationship(
        "FrameworkStandard", back_populates="framework_version", lazy="select"
    )
    applicability_rules: Mapped[list[ApplicabilityRule]] = relationship(
        "ApplicabilityRule", back_populates="framework_version", lazy="select"
    )
