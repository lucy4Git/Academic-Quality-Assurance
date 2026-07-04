"""Embedding service for knowledge chunk vectorisation.

DEVELOPMENT-ONLY PLACEHOLDER
-----------------------------
This module provides a deterministic, dependency-free embedding function
suitable for local development and testing.  It does NOT produce semantically
meaningful vectors — search results will be based on hash similarity, not
semantic meaning.

To replace with real embeddings:
  1. Install sentence-transformers or configure an OpenAI API key.
  2. Subclass or replace ``EmbeddingService`` with your implementation.
  3. The interface (``embed_texts``) remains unchanged; only the model changes.
  4. Collect dimension from ``EmbeddingService.DIMENSIONS`` — Qdrant
     collections must be recreated if dimensions change.

Production embedding options (from KNOWLEDGE_INDEXING_ENGINE.md):
  - sentence-transformers/all-mpnet-base-v2   (768 dims, local)
  - sentence-transformers/all-MiniLM-L6-v2    (384 dims, local, faster)
  - text-embedding-3-small (OpenAI)            (1536 dims, API)
"""

from __future__ import annotations

import hashlib
import logging
import math
import struct

logger = logging.getLogger(__name__)

# Dimensions must match what Qdrant collections are created with.
# Placeholder uses 384 (same as all-MiniLM-L6-v2) so a drop-in replacement
# with that model requires no collection schema change.
EMBEDDING_DIMENSIONS = 384

_DEV_WARNING_EMITTED = False


def _deterministic_embedding(text: str) -> list[float]:
    """Return a 384-dim unit vector derived deterministically from SHA-256(text).

    Algorithm:
      1. Compute SHA-256 of the UTF-8 encoded text.
      2. Repeat the 32-byte digest until we have >= 384 * 4 bytes.
      3. Unpack as IEEE 754 floats, map from [0, 1] range.
      4. Normalise to unit length so cosine similarity works.

    Two chunks with the same text always produce identical vectors.
    Two chunks with different texts produce different vectors.
    The vectors have NO semantic meaning — they are hash-derived only.
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Build floats by treating each 2 bytes as an unsigned int, mapping to [-1, 1].
    # This avoids NaN/Inf values that raw 4-byte float unpacking can produce.
    pairs = [digest[i] * 256 + digest[i + 1] for i in range(0, len(digest) - 1, 1)]
    # Extend to required dimensions by re-hashing progressively
    values: list[float] = []
    seed = digest
    while len(values) < EMBEDDING_DIMENSIONS:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed) - 1, 2):
            raw = seed[i] * 256 + seed[i + 1]  # 0–65535
            values.append((raw / 32767.5) - 1.0)  # map to [-1, 1]
            if len(values) == EMBEDDING_DIMENSIONS:
                break

    magnitude = math.sqrt(sum(v * v for v in values))
    if magnitude == 0.0:
        return [0.0] * EMBEDDING_DIMENSIONS
    return [v / magnitude for v in values]


class EmbeddingService:
    """Provides text → vector embeddings for IKP knowledge chunks.

    This is the development placeholder implementation.  Replace by setting
    ``USE_REAL_EMBEDDINGS=True`` in ``backend/.env`` once a model is available.
    """

    DIMENSIONS: int = EMBEDDING_DIMENSIONS
    IS_PLACEHOLDER: bool = True
    MODEL_NAME: str = "dev-deterministic-sha256-384d"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return a list of float vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            Parallel list of ``DIMENSIONS``-dimension float vectors.
        """
        global _DEV_WARNING_EMITTED
        if not _DEV_WARNING_EMITTED:
            logger.warning(
                "DEVELOPMENT PLACEHOLDER: Using deterministic hash-based embeddings. "
                "Semantic search will NOT return meaningful results. "
                "Replace EmbeddingService with a real model for production use."
            )
            _DEV_WARNING_EMITTED = True

        return [_deterministic_embedding(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query string."""
        return self.embed_texts([query])[0]


# Module-level singleton — one instance per process.
embedding_service = EmbeddingService()
