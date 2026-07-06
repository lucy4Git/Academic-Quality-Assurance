"""Context builder — numbered [SOURCE:N] blocks for LLM prompt injection and citation index."""
from __future__ import annotations
from typing import Any

_MAX_CHUNK_TEXT = 600


def build_context(ranked_chunks: list[dict[str, Any]]) -> tuple[str, dict[str, dict[str, Any]]]:
    if not ranked_chunks:
        return "(No institutional sources retrieved for this query.)", {}
    parts: list[str] = []
    citation_index: dict[str, dict[str, Any]] = {}
    for i, chunk in enumerate(ranked_chunks, start=1):
        key = f"SOURCE:{i}"
        title = chunk.get("title") or chunk.get("entity_id") or "—"
        entity_type = chunk.get("entity_type", "unknown").upper()
        text = (chunk.get("text") or "")[:_MAX_CHUNK_TEXT]
        source_doc = chunk.get("source_document") or "IKP"
        score = chunk.get("combined_score", chunk.get("score", 0.0))
        parts.append(
            f"[{key}] {entity_type}: {title}\n{text}\n(Document: {source_doc}, Score: {score:.2f})"
        )
        citation_index[key] = {
            "source_id": key,
            "title": title,
            "entity_type": chunk.get("entity_type", "unknown"),
            "snippet": (chunk.get("text") or "")[:200],
            "relevance_score": round(float(score), 4),
            "source_document": source_doc,
            "institution_code": chunk.get("institution_code", ""),
        }
    return "\n\n".join(parts), citation_index
