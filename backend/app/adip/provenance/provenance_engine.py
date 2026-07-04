"""ADIP Provenance Engine.

Creates ProvenanceAnchor data objects for every extraction candidate.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from app.adip.mappers.tut_ict_mapper import ExtractionCandidateData
from app.adip.validators.confidence import ConfidenceBreakdown, calculate_confidence


@dataclass
class ProvenanceAnchorData:
    """Data for one provenance anchor — not yet persisted."""

    candidate_index: int  # references position in candidates list
    document_id: str
    institution_id: str
    source_type: str
    source_url: str | None
    source_document_title: str | None
    publisher: str | None
    publisher_verified: bool
    page_number: int | None
    verbatim_quote: str | None
    extraction_method: str
    confidence_score: float
    confidence_breakdown: dict
    academic_year: str | None
    status: str = "active"


def generate_provenance(
    candidates: list[ExtractionCandidateData],
    document_path: Path,
    source_url: str | None,
    source_document_title: str | None,
    publisher: str = "Tshwane University of Technology",
    publisher_verified: bool = True,
    academic_year: str | None = "2026",
) -> list[ProvenanceAnchorData]:
    """Generate one ProvenanceAnchor per candidate."""
    anchors: list[ProvenanceAnchorData] = []

    for i, cand in enumerate(candidates):
        conf = calculate_confidence(
            source_type=cand.provenance_extra.get("source_type", "official_pdf"),
            extraction_method=cand.extraction_method,
            position_clarity=cand.provenance_extra.get("position_clarity", "contextual_label"),
        )

        anchors.append(ProvenanceAnchorData(
            candidate_index=i,
            document_id=cand.document_id,
            institution_id=cand.institution_id,
            source_type=cand.provenance_extra.get("source_type", "official_pdf"),
            source_url=source_url,
            source_document_title=source_document_title,
            publisher=publisher,
            publisher_verified=publisher_verified,
            page_number=cand.source_page,
            verbatim_quote=cand.source_verbatim,
            extraction_method=cand.extraction_method,
            confidence_score=cand.confidence,
            confidence_breakdown={
                "source_weight": conf.source_weight,
                "extraction_weight": conf.extraction_weight,
                "position_weight": conf.position_weight,
                "cross_reference_bonus": conf.cross_reference_bonus,
                "final_score": cand.confidence,
            },
            academic_year=academic_year,
        ))

    return anchors
