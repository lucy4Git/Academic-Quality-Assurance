"""Semantic search over IKP knowledge chunks with tenant isolation.

Tenant isolation rules
----------------------
- SYSTEM_ADMIN may search any active pilot institution by specifying
  institution_code.
- All other roles are locked to their own institution.
- Archived demo institutions (GFU, RCT) are excluded from search.
- Cross-institution search is blocked at this layer (HTTP 403).

The actual institutional boundary enforcement is done by the route handler
(routes/knowledge_index.py) before this service is called.  This service
receives an already-validated collection name and executes the query.
"""

from __future__ import annotations

import logging
from typing import Any

from app.knowledge_indexing.embedding_service import embedding_service
from app.knowledge_indexing.qdrant_service import collection_name, qdrant_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Active pilot collection registry
# ---------------------------------------------------------------------------

# Indexed as: (institution_code.upper(), academic_year, ikp_version)
ACTIVE_PILOT_COLLECTIONS: list[tuple[str, str, str]] = [
    ("TUT", "2026", "v1.1.0"),
    ("UP", "2026", "v1.0.0"),
]

ACTIVE_INSTITUTION_CODES: set[str] = {code for code, _, _ in ACTIVE_PILOT_COLLECTIONS}


def get_collection_for_institution(institution_code: str) -> str | None:
    """Return the Qdrant collection name for an active pilot institution.

    Returns None if the institution code is not a registered active pilot.
    """
    code = institution_code.upper()
    for inst_code, year, version in ACTIVE_PILOT_COLLECTIONS:
        if inst_code == code:
            return collection_name(inst_code, year, version)
    return None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_knowledge(
    query: str,
    institution_code: str,
    entity_type: str | None = None,
    top_k: int = 10,
    min_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    """Search IKP knowledge chunks for a single institution.

    Args:
        query: Natural language or keyword search query.
        institution_code: Institution to search (e.g. "TUT").
        entity_type: Optional filter to a specific entity type
                     (e.g. "programme", "module").
        top_k: Number of results to return (max 50).
        min_confidence: Minimum confidence_score of returned results.

    Returns:
        List of result dicts each containing:
            score, entity_type, entity_id, title, text, source_document,
            provenance_id, confidence_score, institution_code, academic_year,
            ikp_version.

    Raises:
        ValueError: If the institution is not an active pilot or collection
                    does not exist in Qdrant.
    """
    code = institution_code.upper()
    coll = get_collection_for_institution(code)
    if coll is None:
        raise ValueError(
            f"Institution '{code}' is not a registered active pilot institution. "
            f"Active pilots: {sorted(ACTIVE_INSTITUTION_CODES)}"
        )

    if not qdrant_service.collection_exists(coll):
        raise ValueError(
            f"Qdrant collection '{coll}' has not been indexed yet. "
            "Run: python -m app.knowledge_indexing.index_ikp_chunks "
            f"--institution {code}"
        )

    top_k = min(top_k, 50)

    query_vector = embedding_service.embed_query(query)

    filters: dict[str, Any] = {}
    if entity_type:
        filters["entity_type"] = entity_type

    raw_results = qdrant_service.search(
        collection=coll,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=0.0,
        filters=filters if filters else None,
    )

    results = []
    for r in raw_results:
        payload = r["payload"]
        confidence = float(payload.get("confidence_score", 0.0))
        if confidence < min_confidence:
            continue
        results.append(
            {
                "score": round(r["score"], 6),
                "entity_type": payload.get("entity_type", ""),
                "entity_id": payload.get("entity_id", ""),
                "title": payload.get("title", ""),
                "text": payload.get("text", ""),
                "source_document": payload.get("source_document", ""),
                "provenance_id": payload.get("provenance_id", ""),
                "confidence_score": confidence,
                "institution_code": payload.get("institution_code", code),
                "academic_year": payload.get("academic_year", ""),
                "ikp_version": payload.get("ikp_version", ""),
            }
        )

    return results
