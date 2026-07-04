"""ADIP Document Registry model.

Stores one record per registered source document (PDF, DOCX, HTML, etc.).
Every document is hashed on receipt; duplicate hashes within the same institution
are detected and handled before a new record is inserted.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.institution import Institution


class ADIPDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registry entry for one source document in ADIP."""

    __tablename__ = "adip_documents"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── File identity ──────────────────────────────────────────────────────
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)

    # ── Storage ─────────────────────────────────────────────────────────────
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Classification ───────────────────────────────────────────────────────
    document_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)

    # ── Metadata ─────────────────────────────────────────────────────────────
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Processing state ─────────────────────────────────────────────────────
    processing_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )

    # ── Provenance ─────────────────────────────────────────────────────────
    registered_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_official_source: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    institution: Mapped[Institution] = relationship("Institution", foreign_keys=[institution_id], lazy="raise")

    def __repr__(self) -> str:
        return f"<ADIPDocument {self.original_filename!r} state={self.processing_state}>"
