"""Intelligent document classifier with confidence scoring and reason reporting.

Replaces the simple keyword-map classifier for Wave 3 extraction.
Returns document_type, confidence, classification_reason, and matched_terms.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DOCUMENT_TYPES = [
    "institution_homepage",
    "faculty_page",
    "school_page",
    "department_page",
    "programme_page",
    "qualification_page",
    "module_page",
    "policy_document",
    "academic_calendar",
    "prospectus",
    "handbook",
    "rules_regulations",
    "assessment_policy",
    "teaching_learning_policy",
    "research_policy",
    "accreditation_page",
    "contact_page",
    "annual_report",
    "strategic_plan",
    "qa_document",
    "other",
]

# Each rule: (pattern, doc_type, weight)
# Higher weight = stronger signal
_RULES: list[tuple[re.Pattern, str, float]] = [
    # Homepage
    (re.compile(r"\bhome\b|\bwelcome to\b|\bhomepage\b", re.I), "institution_homepage", 0.6),
    # Faculty
    (re.compile(r"\bfaculty of\b|\bfaculty page\b", re.I), "faculty_page", 0.85),
    (re.compile(r"/faculty[/-]", re.I), "faculty_page", 0.5),
    # School
    (re.compile(r"\bschool of\b|\bschool page\b", re.I), "school_page", 0.8),
    (re.compile(r"/school[/-]", re.I), "school_page", 0.5),
    # Department
    (re.compile(r"\bdepartment of\b|\bdepartment page\b", re.I), "department_page", 0.8),
    (re.compile(r"/department[/-]|\bdept\b", re.I), "department_page", 0.5),
    # Programme
    (re.compile(r"\bprogramme[s]?\b|\bprogram[s]?\b", re.I), "programme_page", 0.7),
    (re.compile(r"/programme[s]?[/-]|/program[s]?[/-]", re.I), "programme_page", 0.6),
    # Qualification
    (re.compile(r"\bqualification[s]?\b|\bnqf level\b|\bbtechology\b|\bbachelor of\b|\bmaster of\b|\bdoctor of\b|\bhonours\b|\bdiploma\b|\bcertificate\b", re.I), "qualification_page", 0.75),
    # Module
    (re.compile(r"\bmodule[s]?\b|\bmodule code\b|\bcredits?\b.*\bnqf\b", re.I), "module_page", 0.75),
    (re.compile(r"/module[s]?[/-]", re.I), "module_page", 0.6),
    # Policy (generic)
    (re.compile(r"\bpolic(?:y|ies)\b", re.I), "policy_document", 0.7),
    (re.compile(r"\.pdf$|/policy|/policies", re.I), "policy_document", 0.5),
    # Assessment policy
    (re.compile(r"\bassessment polic", re.I), "assessment_policy", 0.95),
    (re.compile(r"\bassessment\b.*\bpolic", re.I), "assessment_policy", 0.8),
    # Teaching & learning policy
    (re.compile(r"\bteaching.{0,10}learning polic|\bteaching.{0,10}learning strateg", re.I), "teaching_learning_policy", 0.95),
    # Research policy
    (re.compile(r"\bresearch polic|\bresearch strateg|\bresearch plan\b", re.I), "research_policy", 0.9),
    # Academic calendar
    (re.compile(r"\bacademic calendar\b|\bacademic year\b.*\bsemester\b", re.I), "academic_calendar", 0.9),
    (re.compile(r"\bcalendar\b", re.I), "academic_calendar", 0.4),
    # Prospectus
    (re.compile(r"\bprospectus\b", re.I), "prospectus", 0.95),
    # Handbook
    (re.compile(r"\bhandbook\b|\bstudent guide\b", re.I), "handbook", 0.9),
    # Rules & regulations
    (re.compile(r"\brules? and regulation|\brules? of order|\bstatute[s]?\b", re.I), "rules_regulations", 0.9),
    # Accreditation
    (re.compile(r"\baccreditation\b|\bheqc\b|\bsaqa\b|\bche\b|\bdhet\b", re.I), "accreditation_page", 0.8),
    # Contact
    (re.compile(r"\bcontact us\b|\bcontact information\b|\bget in touch\b", re.I), "contact_page", 0.85),
    (re.compile(r"/contact[s]?[/-]?$", re.I), "contact_page", 0.75),
    # Annual report
    (re.compile(r"\bannual report\b", re.I), "annual_report", 0.95),
    # Strategic plan
    (re.compile(r"\bstrategic plan\b|\bstrategic framework\b|\binstitutional plan\b", re.I), "strategic_plan", 0.95),
    # QA document
    (re.compile(r"\bquality assurance\b|\bqa polic|\bquality management\b|\bquality enhancement\b", re.I), "qa_document", 0.85),
]

# URL-path priority rules checked before content rules (very high confidence)
_URL_RULES: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r"^/?$|/index\.html?$|/home/?$", re.I), "institution_homepage", 0.9),
    (re.compile(r"/contact", re.I), "contact_page", 0.9),
    (re.compile(r"/prospectus", re.I), "prospectus", 0.95),
    (re.compile(r"/calendar", re.I), "academic_calendar", 0.85),
    (re.compile(r"/annual.?report", re.I), "annual_report", 0.95),
    (re.compile(r"/strategic.?plan", re.I), "strategic_plan", 0.95),
]


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    classification_reason: str
    matched_terms: list[str]


def classify_intelligently(
    url: str,
    title: str | None = None,
    text_sample: str | None = None,
) -> ClassificationResult:
    """Classify a document into an academic document type with confidence."""
    corpus = "\n".join(filter(None, [url, title or "", (text_sample or "")[:3000]]))
    path = url.split("?")[0].split("#")[0]

    scores: dict[str, float] = {}
    matched: dict[str, list[str]] = {}

    # URL path rules first
    for pattern, doc_type, weight in _URL_RULES:
        if pattern.search(path):
            scores[doc_type] = max(scores.get(doc_type, 0.0), weight)
            matched.setdefault(doc_type, []).append(f"url:{pattern.pattern}")

    # Content rules
    for pattern, doc_type, weight in _RULES:
        m = pattern.search(corpus)
        if m:
            scores[doc_type] = min(1.0, scores.get(doc_type, 0.0) + weight * 0.5)
            term = m.group(0)[:60].strip()
            if term not in matched.get(doc_type, []):
                matched.setdefault(doc_type, []).append(term)

    if not scores:
        return ClassificationResult(
            document_type="other",
            confidence=0.3,
            classification_reason="No matching patterns found",
            matched_terms=[],
        )

    best_type = max(scores, key=lambda t: scores[t])
    confidence = min(1.0, scores[best_type])
    terms = matched.get(best_type, [])[:5]
    reason = f"Matched {len(terms)} pattern(s): {', '.join(terms[:3])}"

    return ClassificationResult(
        document_type=best_type,
        confidence=round(confidence, 3),
        classification_reason=reason,
        matched_terms=terms,
    )
