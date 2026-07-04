"""ADIP Document Classifier.

Three-pass classification:
  1. Admin-provided hint (if given)
  2. Filename heuristics
  3. Content sampling from extracted chunks
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.adip.extractors.base import ExtractionResult


DOCUMENT_TYPES = [
    "prospectus_faculty",
    "prospectus_institution",
    "academic_calendar",
    "policy_examination",
    "policy_assessment",
    "policy_wil",
    "policy_rpl",
    "regulations_student",
    "regulations_academic",
    "programme_guide",
    "module_guide",
    "qualification_specification",
    "assessment_brief",
    "marking_guide",
    "marking_rubric",
    "moderation_internal",
    "moderation_external",
    "attendance_register",
    "learner_evidence",
    "lecturer_evidence",
    "approval_signoff",
    "accreditation_evidence",
    "certificate",
    "transcript",
    "unknown",
]

# Filename keyword signals per type
_FILENAME_SIGNALS: dict[str, list[str]] = {
    "prospectus_faculty": ["prospectus", "part2", "part3", "part4", "part5", "part6", "part7", "part8", "part10"],
    "prospectus_institution": ["prospectus", "part1"],
    "academic_calendar": ["calendar", "academic", "schedule"],
    "policy_examination": ["examination", "exam", "chapter_4", "chapter4"],
    "regulations_student": ["student", "rules", "regulations", "part1"],
    "module_guide": ["module", "guide", "study"],
    "assessment_brief": ["assessment", "brief", "task"],
    "marking_guide": ["marking", "guide", "rubric", "memo"],
    "attendance_register": ["attendance", "register"],
    "certificate": ["certificate"],
    "transcript": ["transcript", "academic_record"],
}

# Content keyword signals per type
_CONTENT_SIGNALS: dict[str, list[str]] = {
    "prospectus_faculty": [
        "nqf level", "admission point", "aps", "credits", "programme", "diploma",
        "faculty of", "bachelor", "postgraduate", "duration",
    ],
    "academic_calendar": [
        "semester", "registration", "examination", "vacation", "recess", "graduation",
    ],
    "policy_examination": [
        "supplementary", "pass mark", "re-examination", "deferral", "invigilation",
        "academic dishonesty", "plagiarism",
    ],
    "regulations_student": [
        "student", "conduct", "disciplinary", "academic exclusion", "readmission",
    ],
    "assessment_brief": [
        "assessment task", "weighting", "due date", "submission", "marks", "rubric",
    ],
    "marking_guide": [
        "total marks", "criteria", "descriptor", "performance level", "rubric",
    ],
    "attendance_register": [
        "attendance", "signature", "absent", "present", "student number",
    ],
    "module_guide": [
        "learning outcomes", "module content", "prescribed", "contact sessions",
    ],
}


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    method: str
    signals_found: list[str]


# Institution-specific filename overrides (applied before all other passes).
# Key: lowercase stem substring to match; value: (doc_type, confidence).
_INSTITUTION_OVERRIDES: dict[str, tuple[str, float]] = {
    # TUT academic calendar files
    "academiccalendar":       ("academic_calendar", 0.97),
    "academic-core-calendar": ("academic_calendar", 0.97),
    "academiccore":           ("academic_calendar", 0.97),
    "academicplanning":       ("academic_calendar", 0.96),
    "academic_planning":      ("academic_calendar", 0.96),
    "sem1-2026":              ("academic_calendar", 0.88),
    "sem2-2026":              ("academic_calendar", 0.88),
    # TUT examination policy
    "chapter_4":              ("policy_examination", 0.96),
    "chapter-4":              ("policy_examination", 0.96),
    "examinationrules":       ("policy_examination", 0.95),
    # TUT student rules
    "students_rules":         ("regulations_student", 0.96),
    "part1_students":         ("regulations_student", 0.96),
    # TUT enrolment info
    "first-year":             ("prospectus_faculty", 0.85),
    "first_year":             ("prospectus_faculty", 0.85),
    "enrolment":              ("prospectus_faculty", 0.80),
}


def classify_document(
    filename: str,
    extraction_result: ExtractionResult | None = None,
    admin_hint: str | None = None,
) -> ClassificationResult:
    """Classify a document using three-pass approach."""

    # Pass 1: Admin-provided hint
    if admin_hint and admin_hint.lower() in DOCUMENT_TYPES:
        return ClassificationResult(
            document_type=admin_hint.lower(),
            confidence=0.92,
            method="admin_hint",
            signals_found=[admin_hint],
        )

    # Pass 1b: Institution-specific filename overrides
    fname_lower = filename.lower()
    fname_clean = re.sub(r"[^a-z0-9_\-]", "_", fname_lower)
    for pattern, (override_type, override_conf) in _INSTITUTION_OVERRIDES.items():
        if pattern in fname_clean or pattern in fname_lower:
            return ClassificationResult(
                document_type=override_type,
                confidence=override_conf,
                method="institution_filename_override",
                signals_found=[pattern],
            )

    # Pass 2: Filename heuristics
    fname = filename.lower()
    fname = re.sub(r"[^a-z0-9_]", "_", fname)

    best_type = "unknown"
    best_score = 0
    best_signals: list[str] = []

    for doc_type, keywords in _FILENAME_SIGNALS.items():
        matches = [kw for kw in keywords if kw.replace(" ", "_") in fname or kw in fname]
        if len(matches) > best_score:
            best_score = len(matches)
            best_type = doc_type
            best_signals = matches

    if best_score >= 2:
        return ClassificationResult(
            document_type=best_type,
            confidence=min(0.96, 0.75 + best_score * 0.08),
            method="filename_heuristic",
            signals_found=best_signals,
        )

    # Pass 3: Content sampling
    if extraction_result and extraction_result.useful_chunks:
        sample_text = " ".join(
            c.text.lower() for c in extraction_result.useful_chunks[:50]
        )
        content_scores: dict[str, list[str]] = {}
        for doc_type, keywords in _CONTENT_SIGNALS.items():
            found = [kw for kw in keywords if kw in sample_text]
            if found:
                content_scores[doc_type] = found

        if content_scores:
            best_content_type = max(content_scores, key=lambda t: len(content_scores[t]))
            best_content_signals = content_scores[best_content_type]
            confidence = min(0.90, 0.55 + len(best_content_signals) * 0.07)

            # Merge with filename hint if consistent
            if best_type != "unknown" and best_content_type == best_type:
                confidence = min(0.95, confidence + 0.10)

            return ClassificationResult(
                document_type=best_content_type,
                confidence=confidence,
                method="content_sampling",
                signals_found=best_content_signals,
            )

    # Filename single-match fallback
    if best_score == 1:
        return ClassificationResult(
            document_type=best_type,
            confidence=0.65,
            method="filename_weak",
            signals_found=best_signals,
        )

    return ClassificationResult(
        document_type="unknown",
        confidence=0.30,
        method="no_signal",
        signals_found=[],
    )
