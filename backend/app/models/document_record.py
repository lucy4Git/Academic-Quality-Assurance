"""DocumentRecord ORM model.

Stores the result of text-extraction and classification for a single uploaded
file.  There is exactly one DocumentRecord per File (1:1 relationship).

The extracted_text column holds the full text content returned by the parser.
For large documents this can be several hundred kilobytes; PostgreSQL TEXT
handles this without issue.  A future stage will chunk and embed this text
into Qdrant for semantic search and AI-agent reasoning.

metadata_json (JSONB) stores format-specific structured data:
  PDF   : {"page_count": N, "headings": [...]}
  DOCX  : {"headings": [...], "tables": [[[cell, ...], ...], ...]}
  XLSX  : {"sheet_names": [...], "row_count": N, "col_count": N}
  PPTX  : {"slide_count": N, "slide_titles": [...]}
  ZIP   : {"contained_files": [...], "parseable_count": N}
  Image : {"width": N, "height": N, "ocr_confidence": 0.0–100.0}
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FileCategory, ProcessingStatus

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.institution import Institution


class DocumentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Text-extraction and classification result for one uploaded file."""

    __tablename__ = "document_records"

    # ------------------------------------------------------------------
    # Tenant + ownership
    # ------------------------------------------------------------------

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Processing lifecycle
    # ------------------------------------------------------------------

    status: Mapped[ProcessingStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Extracted content
    # ------------------------------------------------------------------

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language_detected: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )

    # Structured metadata (headings, tables, sheet names, etc.)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ------------------------------------------------------------------
    # Classification result
    # ------------------------------------------------------------------

    classification: Mapped[FileCategory | None] = mapped_column(
        String(40), nullable=True
    )
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    file: Mapped[File] = relationship(
        "File",
        foreign_keys=[file_id],
        lazy="raise",
    )
    institution: Mapped[Institution] = relationship(
        "Institution",
        foreign_keys=[institution_id],
        lazy="raise",
    )
