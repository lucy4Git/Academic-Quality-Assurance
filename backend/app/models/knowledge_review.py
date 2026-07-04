"""ORM models for the Knowledge Review Centre.

Two tables:
  - knowledge_review_batches  — a batch of extracted candidates awaiting review
  - knowledge_review_items    — individual field-level review items within a batch
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ReviewBatchStatus, ReviewItemStatus


class KnowledgeReviewBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A named batch grouping knowledge review items from a single ADIP extraction run."""

    __tablename__ = "knowledge_review_batches"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ikp_version: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    faculty_scope: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ReviewBatchStatus.OPEN.value
    )
    source_extraction_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    export_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    items: Mapped[list[KnowledgeReviewItem]] = relationship(
        "KnowledgeReviewItem",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="select",
    )


class KnowledgeReviewItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single field-level extracted value awaiting QA officer review."""

    __tablename__ = "knowledge_review_items"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_review_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_value: Mapped[str] = mapped_column(Text, nullable=False)
    edited_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_method: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance_anchor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ReviewItemStatus.PENDING_REVIEW.value, index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ikp_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    batch: Mapped[KnowledgeReviewBatch] = relationship(
        "KnowledgeReviewBatch",
        back_populates="items",
        lazy="select",
    )
