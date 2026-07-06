"""Citation verifier — extract [SOURCE:N] refs, flag unsupported claims, assign grounding_status."""
from __future__ import annotations
import re
from typing import Any

_CITATION_RE = re.compile(r"\[SOURCE:(\d+)\]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_FACTUAL_INDICATORS = re.compile(
    r"\b(is|are|was|were|has|have|had|requires?|must|shall|will|should|"
    r"provides?|contains?|includes?|specifies?|states?|mandates?)\b",
    re.IGNORECASE,
)
_META_PREFIXES = (
    "note:", "no institutional source", "based on the", "according to",
    "the institutional knowledge", "no relevant", "i cannot", "i don't",
    "i do not", "as an ai", "please note",
)


def verify_citations(
    answer: str,
    citation_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not citation_index:
        return {"citations": [], "unsupported_claims": [], "grounding_status": "no_source_found"}

    cited_keys: set[str] = set()
    for m in _CITATION_RE.finditer(answer):
        cited_keys.add(f"SOURCE:{m.group(1)}")

    citations: list[dict[str, Any]] = []
    for key in sorted(cited_keys):
        if key in citation_index:
            citations.append(citation_index[key])

    unsupported: list[str] = []
    sentences = _SENTENCE_SPLIT_RE.split(answer)
    for sentence in sentences:
        s = sentence.strip()
        if not s or len(s) < 20:
            continue
        lower = s.lower()
        if any(lower.startswith(p) for p in _META_PREFIXES):
            continue
        if not _FACTUAL_INDICATORS.search(s):
            continue
        if _CITATION_RE.search(s):
            continue
        unsupported.append(s[:250])

    if citations and not unsupported:
        grounding_status = "grounded"
    elif citations:
        grounding_status = "partially_grounded"
    else:
        grounding_status = "partially_grounded"

    return {
        "citations": citations,
        "unsupported_claims": unsupported[:5],
        "grounding_status": grounding_status,
    }
