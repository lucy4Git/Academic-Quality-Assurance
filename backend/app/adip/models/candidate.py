"""ADIP Extraction Candidate model.

Each candidate represents a proposed mapping from extracted document text
to a specific field of a specific IKP entity.  Candidates are confidence-gated
before being promoted to the official IKP.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.adip.models.chunk import ADIPDocumentChunk
    from app.adip.models.document import ADIPDocument


class ADIPExtractionCandidate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One proposed IKP field value extracted from a document."""

    __tablename__ = "adip_extraction_candidates"

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
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("adip_document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── IKP target ────────────────────────────────────────────────────────
    ikp_entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    ikp_entity_key: Mapped[str] = mapped_column(String(255), nullable=False)
    ikp_field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Extracted value ────────────────────────────────────────────────────
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    coerced_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")

    # ── Source location ────────────────────────────────────────────────────
    extraction_method: Mapped[str] = mapped_column(String(60), nullable=False)
    source_verbatim: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Confidence ────────────────────────────────────────────────────────
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Review state ──────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="proposed", index=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    document: Mapped[ADIPDocument] = relationship(
        "ADIPDocument", foreign_keys=[document_id], lazy="raise"
    )
    chunk: Mapped[ADIPDocumentChunk | None] = relationship(
        "ADIPDocumentChunk", foreign_keys=[chunk_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<ADIPExtractionCandidate {self.ikp_entity_type}.{self.ikp_field_name}"
            f"={self.raw_value!r} conf={self.confidence:.2f} status={self.status}>"
        )
