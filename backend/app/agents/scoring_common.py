"""Shared scoring primitives for two-component compliance agents.

Introduced in Stage 9 by extracting the scoring framework first built for the
Assessment Compliance Agent (Stage 8) so the Moderation Compliance Agent
(Stage 9) — and any future two-component agent — can reuse it without
duplication.

Every two-component agent follows the same shape:

    overall_score = presence_score * PRESENCE_WEIGHT + quality_score * QUALITY_WEIGHT

where ``presence_score`` is a weighted document-checklist percentage and
``quality_score`` is a weighted text-probe pass-rate percentage. Both are
0–100. The resulting ``overall_score`` is mapped to an ``AuditStatus`` via the
shared thresholds below — identical to the Module Folder Audit Agent
(Stage 7) thresholds, so all agents report compliance on a consistent scale.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.models.enums import AuditStatus, FileCategory, FindingSeverity, FindingType

# ---------------------------------------------------------------------------
# Score weighting
# ---------------------------------------------------------------------------

PRESENCE_WEIGHT = 0.60  # fraction of overall score from document presence
QUALITY_WEIGHT = 0.40   # fraction of overall score from content quality probes


# ---------------------------------------------------------------------------
# AuditStatus thresholds (shared across all compliance agents)
# ---------------------------------------------------------------------------

THRESHOLDS: list[tuple[float, AuditStatus]] = [
    (90.0, AuditStatus.COMPLIANT),
    (70.0, AuditStatus.NEEDS_ATTENTION),
    (50.0, AuditStatus.NON_COMPLIANT),
    (0.0,  AuditStatus.CRITICAL),
]


def derive_audit_status(score: float) -> AuditStatus:
    """Map a 0-100 overall score to an AuditStatus using shared thresholds."""
    for threshold, status in THRESHOLDS:
        if score >= threshold:
            return status
    return AuditStatus.CRITICAL


# ---------------------------------------------------------------------------
# Text probe primitive
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TextProbe:
    """A single content-quality check applied to an extracted document text.

    A probe PASSES if any of ``keywords`` appears (case-insensitive substring
    match) in the document's extracted text. Failing probes generate a
    QUALITY_ISSUE finding using the ``finding_*`` templates.
    """

    probe_id: str
    label: str
    keywords: list[str]
    severity: FindingSeverity
    weight: float
    finding_title: str
    finding_description: str   # may use {filename} placeholder
    recommendation: str


def run_probe(probe: TextProbe, extracted_text: str, has_extraction: bool) -> bool:
    """Return True if the probe passes for the given document text.

    A probe can only pass if the document has completed extraction and its
    text contains at least one of the probe's keywords.
    """
    if not has_extraction or not extracted_text:
        return False
    text_lower = extracted_text.lower()
    return any(kw.lower() in text_lower for kw in probe.keywords)


# ---------------------------------------------------------------------------
# Finding contract (engine -> service)
# ---------------------------------------------------------------------------


@dataclass
class FindingSpec:
    """One finding to be persisted as an ``AuditFinding`` row."""

    finding_type: FindingType
    severity: FindingSeverity
    document_category: FileCategory | None
    file_id: uuid.UUID | None
    title: str
    description: str
    recommendation: str


# ---------------------------------------------------------------------------
# Severity ordering (for sorting findings lists)
# ---------------------------------------------------------------------------

SEVERITY_ORDER: dict[FindingSeverity, int] = {
    s: i for i, s in enumerate(FindingSeverity)
}


def sort_findings(findings: list[FindingSpec]) -> list[FindingSpec]:
    """Sort findings CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO."""
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
