"""Qdrant collection management for IKP vector indexing.

Collection naming convention
----------------------------
One collection per institution-year-version combination:

    {institution_code}_{year}_{version}

Examples:
    tut_2026_v1_1_0   ← TUT IKP 2026 v1.1.0
    up_2026_v1_0_0    ← UP IKP 2026 v1.0.0

Dots in version numbers are replaced with underscores to keep the name a valid
Qdrant collection identifier.

Tenant isolation
----------------
Each institution has its own collection.  Cross-institution reads are prevented
at the search layer (search_service.py) by asserting institution_code matches
the caller's institution.  System Admin is the only role allowed to search
across institutions (by explicitly specifying an institution_code).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.knowledge_indexing.embedding_service import EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------


def collection_name(institution_code: str, academic_year: str, ikp_version: str) -> str:
    """Return the canonical Qdrant collection name for an IKP version.

    >>> collection_name("TUT", "2026", "v1.1.0")
    'tut_2026_v1_1_0'
    >>> collection_name("UP", "2026", "v1.0.0")
    'up_2026_v1_0_0'
    """
    version_safe = ikp_version.replace(".", "_")
    return f"{institution_code.lower()}_{academic_year}_{version_safe}"


# ---------------------------------------------------------------------------
# QdrantService
# ---------------------------------------------------------------------------


class QdrantService:
    """Thin wrapper around QdrantClient for AQAA IKP indexing operations."""

    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30,
            )
        return self._client

    # ------------------------------------------------------------------
    # Collection lifecycle
    # ------------------------------------------------------------------

    def ensure_collection(self, name: str) -> bool:
        """Create collection if it does not already exist.

        Returns True if the collection was newly created, False if it already existed.
        """
        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if name in existing:
            logger.debug("Qdrant collection '%s' already exists.", name)
            return False

        client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection '%s' (%d dims, cosine).", name, EMBEDDING_DIMENSIONS)
        return True

    def delete_collection(self, name: str) -> bool:
        """Delete a collection if it exists.  Returns True if deleted."""
        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if name not in existing:
            return False
        client.delete_collection(name)
        logger.info("Deleted Qdrant collection '%s'.", name)
        return True

    def collection_exists(self, name: str) -> bool:
        """Return True if the collection exists in Qdrant."""
        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        return name in existing

    def get_collection_info(self, name: str) -> dict[str, Any] | None:
        """Return basic info about a collection, or None if it does not exist."""
        if not self.collection_exists(name):
            return None
        client = self._get_client()
        info = client.get_collection(name)
        return {
            "name": name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
            "dimension": info.config.params.vectors.size,
        }

    # ------------------------------------------------------------------
    # Point upsert
    # ------------------------------------------------------------------

    def upsert_points(
        self,
        collection: str,
        point_ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        batch_size: int = 50,
    ) -> int:
        """Upsert vectors into a collection in batches.

        Returns the total number of points upserted.
        """
        client = self._get_client()
        total = 0

        for i in range(0, len(point_ids), batch_size):
            batch_ids = point_ids[i : i + batch_size]
            batch_vecs = vectors[i : i + batch_size]
            batch_payloads = payloads[i : i + batch_size]

            points = [
                qmodels.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, pid)),
                    vector=vec,
                    payload=payload,
                )
                for pid, vec, payload in zip(batch_ids, batch_vecs, batch_payloads)
            ]

            client.upsert(collection_name=collection, points=points)
            total += len(points)
            logger.debug("Upserted batch of %d points into '%s'.", len(points), collection)

        return total

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform a nearest-neighbour search in a collection.

        Args:
            collection: Qdrant collection name.
            query_vector: Query embedding vector.
            top_k: Maximum number of results.
            score_threshold: Minimum cosine similarity score (0.0–1.0).
            filters: Optional Qdrant filter dict applied server-side.

        Returns:
            List of result dicts with ``score``, ``payload``, and ``id`` keys.
        """
        client = self._get_client()

        qdrant_filter = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                must_conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=value),
                    )
                )
            qdrant_filter = qmodels.Filter(must=must_conditions)

        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload or {},
            }
            for r in results
        ]


# Module-level singleton.
qdrant_service = QdrantService()
