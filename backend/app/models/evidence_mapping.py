"""EvidenceMapping ORM model — Phase C."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MappingSource, MappingValidationStatus


class EvidenceMapping(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Links an evidence item (file or audit run) to a framework evidence requirement.

    A single file may satisfy requirements across multiple frameworks via
    separate mapping rows. This enables evidence reuse without double-counting.

    mapping_source tracks whether the link was created manually, by rules,
    by semantic search, or by AI assistance — enabling auditability.
    """

    __tablename__ = "evidence_mappings"

    # Tenant scoping
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Framework location
    framework_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_standards.id", ondelete="SET NULL"),
        nullable=True,
    )
    criterion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_criteria.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Evidence source (file or audit run evidence item)
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scope
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="SET NULL"),
        nullable=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Mapping metadata
    mapping_source: Mapped[MappingSource] = mapped_column(
        String(30), default=MappingSource.MANUAL, nullable=False
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[MappingValidationStatus] = mapped_column(
        String(20), default=MappingValidationStatus.PROPOSED, nullable=False, index=True
    )

    # Human review
    validated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    validation_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
