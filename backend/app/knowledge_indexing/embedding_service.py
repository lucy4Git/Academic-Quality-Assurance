"""Embedding service for knowledge chunk vectorisation.

Implementations available, selected by EMBEDDING_PROVIDER in backend/.env:

  USE_REAL_EMBEDDINGS=false (default)
    → PlaceholderEmbeddingService: deterministic SHA-256 hash vectors, 384 dims.
      No API calls. Semantic search returns random-ish results. Dev only.

  USE_REAL_EMBEDDINGS=true, EMBEDDING_PROVIDER=fastembed  (recommended)
    → FastEmbedEmbeddingService: ONNX-based local model, no PyTorch required.
      Default model: BAAI/bge-small-en-v1.5 (384 dims). No API key.
      Model downloaded on first use (~45 MB). Works in Docker python:3.13-slim.

  USE_REAL_EMBEDDINGS=true, EMBEDDING_PROVIDER=sentence_transformers
    → SentenceTransformerEmbeddingService: local model via sentence-transformers.
      Default model: all-MiniLM-L6-v2 (384 dims). Requires torch (~2 GB).

  USE_REAL_EMBEDDINGS=true, EMBEDDING_PROVIDER=openai
    → OpenAIEmbeddingService: text-embedding-3-small (1536 dims).
      Requires OPENAI_API_KEY with active billing.

IMPORTANT: Qdrant collections are dimension-specific. If you change provider
and the dimensions differ, run:
    python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate
"""

from __future__ import annotations

import hashlib
import logging
import math

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Placeholder implementation (384 dims, no API)
# ---------------------------------------------------------------------------

PLACEHOLDER_DIMENSIONS = 384


def _deterministic_embedding(text: str) -> list[float]:
    values: list[float] = []
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    while len(values) < PLACEHOLDER_DIMENSIONS:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed) - 1, 2):
            raw = seed[i] * 256 + seed[i + 1]
            values.append((raw / 32767.5) - 1.0)
            if len(values) == PLACEHOLDER_DIMENSIONS:
                break
    magnitude = math.sqrt(sum(v * v for v in values))
    if magnitude == 0.0:
        return [0.0] * PLACEHOLDER_DIMENSIONS
    return [v / magnitude for v in values]


class PlaceholderEmbeddingService:
    """Hash-based deterministic embeddings. No semantic meaning. Dev only."""

    DIMENSIONS: int = PLACEHOLDER_DIMENSIONS
    IS_PLACEHOLDER: bool = True
    MODEL_NAME: str = "dev-deterministic-sha256-384d"

    _warned: bool = False

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not PlaceholderEmbeddingService._warned:
            logger.warning(
                "PLACEHOLDER EMBEDDINGS active. Set USE_REAL_EMBEDDINGS=true for semantic search."
            )
            PlaceholderEmbeddingService._warned = True
        return [_deterministic_embedding(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# Sentence-transformers implementation (local, no API key)
# ---------------------------------------------------------------------------

SENTENCE_TRANSFORMER_DIMENSIONS = 384  # all-MiniLM-L6-v2 default


class SentenceTransformerEmbeddingService:
    """Real semantic embeddings via sentence-transformers (local model, no API key)."""

    IS_PLACEHOLDER: bool = False

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer  # lazy import
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        self.DIMENSIONS: int = self._model.get_sentence_embedding_dimension()
        self.MODEL_NAME: str = model_name
        logger.info("Loaded sentence-transformers model '%s' (%d dims)", model_name, self.DIMENSIONS)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# OpenAI implementation (1536 dims, requires API key with billing)
# ---------------------------------------------------------------------------

OPENAI_DIMENSIONS = 1536


class OpenAIEmbeddingService:
    """Real semantic embeddings via OpenAI text-embedding-3-small (1536 dims)."""

    DIMENSIONS: int = OPENAI_DIMENSIONS
    IS_PLACEHOLDER: bool = False
    MODEL_NAME: str = "text-embedding-3-small"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        from openai import OpenAI  # lazy import
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_texts(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            results.extend(item.embedding for item in response.data)
        return results

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# FastEmbed implementation (ONNX-based, no PyTorch, works in slim containers)
# ---------------------------------------------------------------------------

FASTEMBED_DIMENSIONS = 384  # BAAI/bge-small-en-v1.5 and all-MiniLM-L6-v2


class FastEmbedEmbeddingService:
    """Real semantic embeddings via fastembed (ONNX, no PyTorch required).

    Default model: BAAI/bge-small-en-v1.5 (384 dims, ~45 MB).
    Also supports: sentence-transformers/all-MiniLM-L6-v2 (384 dims).
    No API key. Works in Docker python:3.13-slim after `pip install fastembed`.
    """

    IS_PLACEHOLDER: bool = False

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding  # lazy import
        self._model = TextEmbedding(model_name=model_name)
        self._model_name = model_name
        self.MODEL_NAME: str = model_name
        # Probe dimensions by embedding one token
        probe = list(self._model.embed(["probe"]))
        self.DIMENSIONS: int = len(probe[0])
        logger.info("Loaded fastembed model '%s' (%d dims)", model_name, self.DIMENSIONS)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._model.embed(texts)]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# HuggingFace Inference API implementation (httpx + numpy, no torch required)
# ---------------------------------------------------------------------------


class HuggingFaceEmbeddingService:
    """Real semantic embeddings via HuggingFace Inference API.

    Uses sentence-transformers/all-MiniLM-L6-v2 by default.
    Requires only httpx and numpy — no torch or SDK packages.
    """

    DIMENSIONS: int = 384
    IS_PLACEHOLDER: bool = False

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", hf_token: str | None = None) -> None:
        import httpx
        import numpy as np  # noqa: F401 — verify available
        self._model_name = model_name
        self.MODEL_NAME = model_name
        self._url = f"https://router.huggingface.co/hf-inference/pipeline/feature-extraction/{model_name}"
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if hf_token:
            self._headers["Authorization"] = f"Bearer {hf_token}"
        self._client = httpx.Client(timeout=60.0)
        logger.info("HuggingFace embedding service: %s (%d dims)", model_name, self.DIMENSIONS)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import numpy as np
        results: list[list[float]] = []
        for i in range(0, len(texts), 32):
            batch = texts[i : i + 32]
            response = self._client.post(
                self._url,
                json={"inputs": batch, "options": {"wait_for_model": True}},
                headers=self._headers,
            )
            response.raise_for_status()
            embeddings = response.json()
            for emb in embeddings:
                arr = np.array(emb, dtype=np.float32)
                norm = float(np.linalg.norm(arr))
                if norm > 0:
                    arr = arr / norm
                results.append(arr.tolist())
        return results

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# Factory — selects implementation from settings
# ---------------------------------------------------------------------------

def get_embedding_service() -> (
    PlaceholderEmbeddingService
    | FastEmbedEmbeddingService
    | SentenceTransformerEmbeddingService
    | OpenAIEmbeddingService
    | HuggingFaceEmbeddingService
):
    """Return the correct embedding service based on settings.

    Priority order when USE_REAL_EMBEDDINGS=true:
    1. EMBEDDING_PROVIDER=fastembed           → ONNX local model (no torch, Docker-safe)
    2. EMBEDDING_PROVIDER=sentence_transformers → local model (needs torch)
    3. EMBEDDING_PROVIDER=huggingface          → HF Inference API (httpx + numpy)
    4. EMBEDDING_PROVIDER=openai               → OpenAI API (billing required)
    5. Fallback                                → PlaceholderEmbeddingService
    """
    from app.config import settings  # avoid circular import at module load

    if not getattr(settings, "USE_REAL_EMBEDDINGS", False):
        return PlaceholderEmbeddingService()

    provider = getattr(settings, "EMBEDDING_PROVIDER", "fastembed").lower()
    model = getattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    if provider == "fastembed":
        try:
            fastembed_model = model if "/" in model else f"BAAI/{model}"
            return FastEmbedEmbeddingService(model_name=fastembed_model)
        except Exception as exc:
            logger.warning("fastembed failed (%s). Trying sentence_transformers.", exc)
            provider = "sentence_transformers"

    if provider == "sentence_transformers":
        try:
            st_model = model.split("/")[-1] if "/" in model else model
            return SentenceTransformerEmbeddingService(model_name=st_model)
        except Exception as exc:
            logger.warning("sentence_transformers failed (%s). Trying huggingface.", exc)
            provider = "huggingface"

    if provider == "huggingface":
        try:
            hf_model = model if "/" in model else f"sentence-transformers/{model}"
            hf_token = getattr(settings, "HF_TOKEN", None)
            return HuggingFaceEmbeddingService(model_name=hf_model, hf_token=hf_token)
        except Exception as exc:
            logger.warning("HuggingFace embedding service failed (%s). Trying openai.", exc)
            provider = "openai"

    if provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if api_key:
            try:
                logger.info("Embedding service: OpenAI %s (%d dims)", model, OPENAI_DIMENSIONS)
                return OpenAIEmbeddingService(api_key=api_key, model=model)
            except Exception as exc:
                logger.warning("OpenAI embedding failed (%s). Falling back to placeholder.", exc)

    logger.warning("All real embedding providers failed. Using placeholder embeddings.")
    return PlaceholderEmbeddingService()


# Module-level singleton — resolved once at import time.
embedding_service = get_embedding_service()

# Active dimensions — imported by qdrant_service.py.
EMBEDDING_DIMENSIONS = embedding_service.DIMENSIONS

# Public alias — callable class that always returns a PlaceholderEmbeddingService.
# Tests import `EmbeddingService` and call it with no args to exercise the placeholder path.
EmbeddingService = PlaceholderEmbeddingService
