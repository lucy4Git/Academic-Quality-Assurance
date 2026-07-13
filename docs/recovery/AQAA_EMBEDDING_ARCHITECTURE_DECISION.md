# AQAA Embedding Architecture Decision

**Document:** AQAA_EMBEDDING_ARCHITECTURE_DECISION  
**Sprint:** Recovery Sprint — Phase 1  
**Date:** 2026-07-13  
**Status:** DECIDED AND IMPLEMENTED

---

## Decision

**Use `fastembed` (Qdrant's ONNX-based embedding library) with model `BAAI/bge-small-en-v1.5` (384 dims) as the production embedding provider for AQAA.**

---

## Context

AQAA requires an embedding service that:
1. Works in the Docker container (`python:3.13-slim` — no PyTorch, no CUDA)
2. Produces real semantic vectors (not hash-based placeholders)
3. Requires no API key or external service dependency
4. Uses identical vectors at index time (host) and query time (Docker container)
5. Produces 384-dim vectors to match the existing Qdrant collection schema

---

## Alternatives Evaluated

### Option 1: sentence-transformers (REJECTED for Docker)
- Model: `all-MiniLM-L6-v2`, 384 dims
- **Problem:** Requires PyTorch (~2 GB). `python:3.13-slim` has no PyTorch. Would require changing the base Docker image.
- **Result:** Works on host (used for intermediate indexing), fails in Docker container at query time.

### Option 2: OpenAI text-embedding-3-small (REJECTED — quota)
- Dimensions: 1536 (incompatible with existing 384-dim collections)
- **Problem:** OpenAI account has `insufficient_quota` error. No billing configured.
- **Problem:** Would require reindexing all collections to 1536 dims, changing Qdrant collection config.
- **Result:** Rejected due to quota and dimension mismatch.

### Option 3: HuggingFace Inference API (REJECTED — authentication)
- Model: `sentence-transformers/all-MiniLM-L6-v2` via HF router endpoint
- **Problem:** HF router now requires authentication for all models (`401 Unauthorized`).
- **Problem:** External API dependency — production risk if HF is unavailable.
- **Result:** Rejected.

### Option 4: Gemini Embeddings (REJECTED — invalid key)
- **Problem:** `GEMINI_API_KEY` has unusual format (`AQ.Ab8R...`). All requests returned 404.
- **Result:** Key appears invalid. Rejected.

### Option 5: fastembed (SELECTED)
- Library: `fastembed>=0.3` (Qdrant's own embedding library)
- Model: `BAAI/bge-small-en-v1.5`, 384 dims
- **Advantages:**
  - ONNX runtime — no PyTorch, no CUDA, works in `python:3.13-slim`
  - 384 dims — matches existing Qdrant collection schema (no reindex dimension change)
  - No API key — fully local, no external dependency
  - Same library installable on host and in Docker: `pip install fastembed`
  - Model cached at `~/.cache/fastembed` (host) and `/root/.cache/fastembed` (container)
  - Model weight: ~45 MB (vs ~90 MB for sentence-transformers)
  - Identical vectors at index time and query time (same ONNX model)

---

## Implementation

**Files modified:**
- `backend/app/knowledge_indexing/embedding_service.py` — added `FastEmbedEmbeddingService`, updated factory
- `backend/app/config.py` — updated defaults: `EMBEDDING_PROVIDER=fastembed`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`
- `backend/.env` — set `EMBEDDING_PROVIDER=fastembed`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`
- `backend/requirements.txt` — added `fastembed>=0.3,<1.0`

**Factory fallback chain (when `USE_REAL_EMBEDDINGS=true`):**
1. `fastembed` → `FastEmbedEmbeddingService` (ONNX, no torch)
2. `sentence_transformers` → `SentenceTransformerEmbeddingService` (needs torch)
3. `huggingface` → `HuggingFaceEmbeddingService` (httpx + numpy, needs HF token)
4. `openai` → `OpenAIEmbeddingService` (needs billing)
5. Fallback → `PlaceholderEmbeddingService` (SHA-256, dev only)

---

## Verification

Post-implementation:
- Host: `FastEmbedEmbeddingService`, 384 dims, `IS_PLACEHOLDER=False` ✓
- Docker: `FastEmbedEmbeddingService`, 384 dims, `IS_PLACEHOLDER=False` ✓
- `is_placeholder_mode: false` in all AI assistant responses ✓
- Qdrant collections reindexed with BAAI/bge-small-en-v1.5 vectors ✓

---

## Future Upgrade Path

If semantic quality needs improvement:
- Upgrade to `BAAI/bge-base-en-v1.5` (768 dims) — requires collection recreation
- Or `BAAI/bge-large-en-v1.5` (1024 dims) — requires collection recreation
- Run: `python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate`
