"""Source ranking for Advanced RAG — re-ranks Qdrant results and enforces cross-tenant isolation."""
from __future__ import annotations
from typing import Any
import logging

logger = logging.getLogger(__name__)

_W_RELEVANCE = 0.7
_W_CONFIDENCE = 0.3
_BOOST_VALUE = 0.05

_ENTITY_BOOST: dict[str, str | None] = {
    "programme_query": "programme",
    "module_query": "module",
    "compliance_query": None,
    "audit_query": None,
    "general": None,
}


def rank_sources(
    chunks: list[dict[str, Any]],
    institution_code: str,
    intent: str = "general",
) -> list[dict[str, Any]]:
    code = institution_code.upper()
    preferred_entity = _ENTITY_BOOST.get(intent)
    ranked: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_code = (chunk.get("institution_code") or "").upper()
        if chunk_code and chunk_code != code:
            logger.warning("source_ranker: cross-tenant chunk rejected (expected=%s, got=%s)", code, chunk_code)
            continue
        relevance = float(chunk.get("score", 0.0))
        confidence = float(chunk.get("confidence_score", 0.0))
        combined = _W_RELEVANCE * relevance + _W_CONFIDENCE * confidence
        if preferred_entity and chunk.get("entity_type") == preferred_entity:
            combined += _BOOST_VALUE
        ranked.append({**chunk, "combined_score": round(min(combined, 1.0), 6)})
    ranked.sort(key=lambda c: c["combined_score"], reverse=True)
    return ranked
