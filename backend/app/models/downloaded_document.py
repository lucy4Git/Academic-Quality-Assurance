from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DownloadedDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "downloaded_documents"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("acquisition_jobs.id", ondelete="SET NULL"), nullable=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("acquisition_sources.id", ondelete="SET NULL"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    content_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="other"
    )
    data_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="needs_review"
    )
    data_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    institution_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institution_documents.id", ondelete="SET NULL"), nullable=True
    )
    # Wave 3 — intelligent extraction fields
    extraction_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending | running | completed | needs_review | failed
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    meaningful_title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
