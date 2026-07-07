"""Rule-based document type classifier using URL and title heuristics."""
from __future__ import annotations

DOCUMENT_TYPES = [
    "policy", "programme", "qualification", "module", "prospectus",
    "calendar", "assessment", "moderation", "teaching", "research",
    "qa", "accreditation", "annual_report", "strategic_plan", "other",
]

KEYWORD_MAP: dict[str, str] = {
    "policy": "policy",
    "policies": "policy",
    "prospectus": "prospectus",
    "programme": "programme",
    "program": "programme",
    "qualification": "qualification",
    "module": "module",
    "calendar": "calendar",
    "assessment": "assessment",
    "moderation": "moderation",
    "teaching": "teaching",
    "research": "research",
    "quality": "qa",
    "accreditation": "accreditation",
    "annual report": "annual_report",
    "annual_report": "annual_report",
    "strategic plan": "strategic_plan",
    "strategic_plan": "strategic_plan",
}


def classify_document(url: str, title: str | None = None) -> str:
    text = f"{url} {title or ''}".lower()
    for keyword, doc_type in KEYWORD_MAP.items():
        if keyword in text:
            return doc_type
    return "other"
