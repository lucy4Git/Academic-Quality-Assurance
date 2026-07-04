"""ADIP confidence scoring engine.

Computes per-field confidence scores based on:
  - Source type (official domain vs secondary)
  - Extraction quality (native text vs OCR vs inference)
  - Position clarity (explicit label vs inferred)
  - Cross-reference bonus (multiple sources agree)
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_TYPE_WEIGHTS: dict[str, float] = {
    "official_html": 1.00,
    "official_pdf": 0.92,
    "official_pdf_ocr": 0.78,
    "uploaded_by_admin": 0.88,
    "uploaded_by_staff": 0.82,
    "heqsf_standard": 0.82,
    "manual_entry_verified": 0.90,
    "manual_entry_unverified": 0.50,
    "secondary_website": 0.45,
    "unknown": 0.30,
}

EXTRACTION_QUALITY_WEIGHTS: dict[str, float] = {
    "verbatim_match": 1.00,
    "regex_clean_text": 0.95,
    "table_cell_identified": 0.90,
    "table_cell_inferred": 0.78,
    "heading_based": 0.85,
    "paragraph_inference": 0.70,
    "ocr_high": 0.82,
    "ocr_medium": 0.70,
    "ocr_low": 0.55,
    "ai_inference": 0.55,
}

POSITION_CLARITY_WEIGHTS: dict[str, float] = {
    "explicit_label": 1.00,       # "NQF Level: 6"
    "column_header": 0.92,        # Table column "NQF Level"
    "contextual_label": 0.80,     # "offered at NQF 6"
    "implicit": 0.65,
}

# Gating thresholds
GATE_AUTO_APPROVE = 0.90
GATE_MEDIUM_REVIEW = 0.70
GATE_QUARANTINE = 0.70  # below this → quarantine


@dataclass
class ConfidenceBreakdown:
    source_type: str
    source_weight: float
    extraction_method: str
    extraction_weight: float
    position_clarity: str
    position_weight: float
    cross_reference_bonus: float
    final_score: float

    def gate(self) -> str:
        """Return the action gate for this confidence score."""
        if self.final_score >= GATE_AUTO_APPROVE:
            return "auto_approved"
        if self.final_score >= GATE_MEDIUM_REVIEW:
            return "pending_review"
        return "quarantined"


def calculate_confidence(
    source_type: str = "official_pdf",
    extraction_method: str = "regex_clean_text",
    position_clarity: str = "explicit_label",
    cross_reference_bonus: float = 0.0,
) -> ConfidenceBreakdown:
    """Compute a field-level confidence score."""
    sw = SOURCE_TYPE_WEIGHTS.get(source_type, 0.30)
    ew = EXTRACTION_QUALITY_WEIGHTS.get(extraction_method, 0.60)
    pw = POSITION_CLARITY_WEIGHTS.get(position_clarity, 0.65)

    raw = sw * ew * pw
    final = min(1.0, raw + cross_reference_bonus)

    return ConfidenceBreakdown(
        source_type=source_type,
        source_weight=sw,
        extraction_method=extraction_method,
        extraction_weight=ew,
        position_clarity=position_clarity,
        position_weight=pw,
        cross_reference_bonus=cross_reference_bonus,
        final_score=round(final, 4),
    )


def gate_status(confidence: float) -> str:
    """Return the gate status string for a given score."""
    if confidence >= GATE_AUTO_APPROVE:
        return "auto_approved"
    if confidence >= GATE_MEDIUM_REVIEW:
        return "pending_review"
    return "quarantined"
