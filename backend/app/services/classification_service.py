"""Document classification service.

Classifies extracted document text against the ``FileCategory`` taxonomy using
a weighted keyword-scoring algorithm.  No ML model is required; the keyword
tables encode institutional knowledge about document types and can be tuned
independently of the service logic.

Scoring algorithm
-----------------
For each ``FileCategory`` a set of keyword/phrase patterns is defined.  The
classifier evaluates three signals, each normalised to [0, 1]:

    1. Filename tokens       — weight 3.0  (filenames are the most reliable signal)
    2. Document head (≤2000 chars) — weight 2.0  (title/intro carries high signal)
    3. Full text             — weight 1.0

The category with the highest weighted score wins.  If the winning score is
below ``CONFIDENCE_THRESHOLD`` (0.20) the result is ``FileCategory.OTHER``.

The returned confidence is the normalised winning score in the range [0.0, 1.0].
It is stored on ``DocumentRecord.classification_confidence`` so audit agents
can apply their own threshold logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.enums import FileCategory

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.20

# ---------------------------------------------------------------------------
# Keyword tables
# Each list entry is a plain string; matching is case-insensitive.
# Longer phrases are preferred over single words for precision.
# ---------------------------------------------------------------------------

_KEYWORDS: dict[FileCategory, list[str]] = {
    FileCategory.COURSE_OUTLINE: [
        "course outline",
        "module outline",
        "study guide",
        "module guide",
        "learning outcomes",
        "module objectives",
        "credit value",
        "credit points",
        "contact hours",
        "prerequisite",
        "co-requisite",
        "lecture schedule",
        "timetable",
        "weekly plan",
        "teaching schedule",
        "reading list",
        "recommended texts",
        "prescribed textbook",
        "course description",
        "module description",
        "nqf level",
        "qualification level",
        "semester overview",
    ],
    FileCategory.ASSESSMENT_BRIEF: [
        "assessment brief",
        "assignment brief",
        "task description",
        "submission requirements",
        "submission deadline",
        "due date",
        "word limit",
        "page limit",
        "assessment instructions",
        "assessment task",
        "student instructions",
        "assignment instructions",
        "what you must do",
        "what to submit",
        "plagiarism declaration",
        "academic integrity",
        "turnitin",
        "late submission",
        "penalty",
        "groupwork",
        "individual assignment",
    ],
    FileCategory.ASSESSMENT_RUBRIC: [
        "rubric",
        "marking rubric",
        "grading rubric",
        "assessment criteria",
        "marking criteria",
        "performance criteria",
        "marking guide",
        "criteria and standards",
        "distinction",
        "merit",
        "credit level",
        "pass level",
        "fail level",
        "exceeds expectations",
        "meets expectations",
        "below expectations",
        "band descriptor",
        "level descriptor",
        "criterion score",
        "weighting",
        "allocated marks",
        "total marks",
    ],
    FileCategory.MARKED_SAMPLE: [
        "marked sample",
        "sample submission",
        "annotated script",
        "feedback on script",
        "marker comments",
        "examiner comments",
        "student work sample",
        "graded work",
        "representative sample",
        "high distinction sample",
        "distinction sample",
        "pass sample",
        "fail sample",
        "moderation sample",
        "borderline sample",
    ],
    FileCategory.INTERNAL_MODERATION: [
        "internal moderation",
        "internal moderator",
        "second marker",
        "double marking",
        "intra-institution moderation",
        "moderation report",
        "moderation findings",
        "moderation summary",
        "mark adjustment",
        "marks verified",
        "moderator signature",
        "moderation completed",
        "agreement between markers",
        "discrepancy",
        "moderation outcome",
        "internal moderation form",
    ],
    FileCategory.EXTERNAL_MODERATION: [
        "external moderation",
        "external moderator",
        "external examiner",
        "external examiner report",
        "external review",
        "cross-institutional moderation",
        "external moderation report",
        "external moderation feedback",
        "moderator from another institution",
        "external panel",
        "institutional benchmarking",
        "external moderation outcome",
        "cross-marking",
    ],
    FileCategory.ATTENDANCE_REGISTER: [
        "attendance register",
        "attendance sheet",
        "sign-in sheet",
        "class register",
        "student attendance",
        "lecture attendance",
        "tutorial attendance",
        "absent",
        "present",
        "student number",
        "student id",
        "signature",
        "date of lecture",
        "attendance record",
        "roll call",
    ],
    FileCategory.ASSESSMENT_MEMO: [
        "memorandum",
        "marking memo",
        "marking memorandum",
        "model answer",
        "suggested answer",
        "expected answer",
        "model solution",
        "examiner memo",
        "answer guide",
        "mark allocation",
        "allocation of marks",
        "total out of",
        "question marks",
        "section marks",
        "per question",
    ],
    FileCategory.STUDENT_FEEDBACK: [
        "student feedback",
        "feedback to students",
        "module feedback",
        "course evaluation",
        "student survey",
        "end of semester survey",
        "student experience",
        "feedback form",
        "student rating",
        "student satisfaction",
        "module evaluation",
        "teaching evaluation",
        "peer feedback",
    ],
    FileCategory.ACCREDITATION_EVIDENCE: [
        "accreditation",
        "accreditation evidence",
        "professional body",
        "accreditation body",
        "programme accreditation",
        "institutional accreditation",
        "quality assurance",
        "heqsf",
        "chee",
        "ecsa",
        "saica",
        "saqa",
        "nqf",
        "qualification review",
        "self-evaluation report",
        "site visit",
        "accreditation panel",
        "compliance evidence",
        "programme review",
        "accreditation submission",
    ],
}

# Filename-level patterns: if a pattern matches the filename (case-insensitive)
# the corresponding category receives a strong boost.
_FILENAME_PATTERNS: list[tuple[re.Pattern[str], FileCategory]] = [
    (re.compile(r"outline|study.?guide|module.?guide", re.I), FileCategory.COURSE_OUTLINE),
    (re.compile(r"brief|assignment", re.I), FileCategory.ASSESSMENT_BRIEF),
    (re.compile(r"rubric|criteria|grading", re.I), FileCategory.ASSESSMENT_RUBRIC),
    (re.compile(r"sample|marked.?script|annotated", re.I), FileCategory.MARKED_SAMPLE),
    (re.compile(r"internal.?mod|second.?mark|intra", re.I), FileCategory.INTERNAL_MODERATION),
    (re.compile(r"external.?mod|external.?exam", re.I), FileCategory.EXTERNAL_MODERATION),
    (re.compile(r"attend|register|sign.?in|roll", re.I), FileCategory.ATTENDANCE_REGISTER),
    (re.compile(r"memo|memorandum|model.?ans|marking.?guide", re.I), FileCategory.ASSESSMENT_MEMO),
    (re.compile(r"feedback|survey|evaluation", re.I), FileCategory.STUDENT_FEEDBACK),
    (re.compile(r"accredit|saqa|heqsf|chee|ecsa", re.I), FileCategory.ACCREDITATION_EVIDENCE),
]


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassificationResult:
    """Outcome of a single classification run."""

    category: FileCategory
    confidence: float       # normalised score in [0.0, 1.0]
    scores: dict[str, float]  # raw per-category scores for diagnostics


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------


def _keyword_score(text: str, keywords: list[str]) -> float:
    """Return fraction of *keywords* found in *text* (case-insensitive)."""
    if not keywords or not text:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return hits / len(keywords)


def classify(text: str, filename: str) -> ClassificationResult:
    """Classify a document by scoring its text against the keyword tables.

    Args:
        text:     Full extracted text.
        filename: Original filename (used for filename heuristics).

    Returns:
        ``ClassificationResult`` with the winning category and confidence.
    """
    head = text[:2000]
    fn_lower = filename.lower()
    scores: dict[str, float] = {}

    for category, keywords in _KEYWORDS.items():
        fn_score = _keyword_score(fn_lower, keywords) * 3.0
        head_score = _keyword_score(head, keywords) * 2.0
        full_score = _keyword_score(text, keywords) * 1.0
        scores[category.value] = fn_score + head_score + full_score

    # Filename pattern boost: adds 1.0 to the matching category.
    for pattern, category in _FILENAME_PATTERNS:
        if pattern.search(filename):
            scores[category.value] = scores.get(category.value, 0.0) + 1.0

    if not scores or max(scores.values()) == 0.0:
        return ClassificationResult(
            category=FileCategory.OTHER,
            confidence=0.0,
            scores=scores,
        )

    max_score = max(scores.values())
    # Normalise: divide by theoretical maximum (3+2+1 per keyword = 6, but we
    # use observed max so the value is relative to competing categories).
    normalised = {k: v / max_score for k, v in scores.items()}

    winning_key = max(normalised, key=lambda k: normalised[k])
    confidence = normalised[winning_key]

    if confidence < CONFIDENCE_THRESHOLD:
        return ClassificationResult(
            category=FileCategory.OTHER,
            confidence=round(confidence, 4),
            scores=scores,
        )

    # Map winning key back to enum.
    winning_category = FileCategory(winning_key)
    return ClassificationResult(
        category=winning_category,
        confidence=round(confidence, 4),
        scores=scores,
    )
