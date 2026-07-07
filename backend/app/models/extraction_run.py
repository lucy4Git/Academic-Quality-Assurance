"""ExtractionRun — tracks one intelligent extraction pass on a downloaded document."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extraction_runs"

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
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending | running | completed | needs_review | failed
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    improved_title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    candidates_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
