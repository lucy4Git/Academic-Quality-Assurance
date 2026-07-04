"""ADIP Document Chunk model.

Stores one text chunk extracted from a source document.
Each chunk has a type, location (page, slide, sheet, cell), and extraction metadata.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.adip.models.document import ADIPDocument


class ADIPDocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One extracted text segment from a registered ADIP document."""

    __tablename__ = "adip_document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("adip_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Content ──────────────────────────────────────────────────────────────
    chunk_type: Mapped[str] = mapped_column(String(40), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Location ─────────────────────────────────────────────────────────────
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    section_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    heading_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Extraction metadata ────────────────────────────────────────────────
    extraction_method: Mapped[str] = mapped_column(String(60), nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped[ADIPDocument] = relationship(
        "ADIPDocument", foreign_keys=[document_id], lazy="raise"
    )

    def __repr__(self) -> str:
        preview = self.text[:40].replace("\n", " ") if self.text else ""
        return f"<ADIPDocumentChunk p={self.page_number} type={self.chunk_type!r} {preview!r}>"
