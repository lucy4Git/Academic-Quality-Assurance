"""ExtractionCandidate — a single metadata field extracted from a document."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionCandidate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extraction_candidates"

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("downloaded_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "faculty_name" | "programme_name" | "module_code" | "contact_email" | "nqf_level"
    extracted_value: Mapped[str] = mapped_column(String(1000), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_snippet: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Entity mapping
    proposed_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36), nullable=True
    )  # stored as str to support multiple entity tables
    proposed_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proposed_entity_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    match_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Review
    mapping_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="needs_review"
    )  # auto_mapped | needs_review | approved | rejected
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="needs_review"
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
