"""ADIP Provenance Anchor model.

One ProvenanceAnchor is created for every ADIPExtractionCandidate.
It records the exact source location — page, paragraph, cell range, verbatim quote —
so that every IKP field value can be traced back to its authoritative source.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.adip.models.candidate import ADIPExtractionCandidate
    from app.adip.models.document import ADIPDocument


class ADIPProvenanceAnchor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Fine-grained source reference for one extracted candidate field."""

    __tablename__ = "adip_provenance_anchors"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("adip_extraction_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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

    # ── Source metadata ────────────────────────────────────────────────────
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_document_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publisher_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Location ──────────────────────────────────────────────────────────
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    section_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    char_offset_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Content ───────────────────────────────────────────────────────────
    verbatim_quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Extraction ────────────────────────────────────────────────────────
    extraction_method: Mapped[str] = mapped_column(String(60), nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extractor_version: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # ── Confidence ────────────────────────────────────────────────────────
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # ── Verification ──────────────────────────────────────────────────────
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Validity ──────────────────────────────────────────────────────────
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # YYYY-MM-DD
    expiry_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    candidate: Mapped[ADIPExtractionCandidate] = relationship(
        "ADIPExtractionCandidate", foreign_keys=[candidate_id], lazy="raise"
    )
    document: Mapped[ADIPDocument] = relationship(
        "ADIPDocument", foreign_keys=[document_id], lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<ADIPProvenanceAnchor doc={self.document_id}"
            f" p={self.page_number} conf={self.confidence_score:.2f}>"
        )
