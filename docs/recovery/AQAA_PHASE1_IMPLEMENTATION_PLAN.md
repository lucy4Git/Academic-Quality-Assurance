# AQAA Phase 1 Implementation Plan

**Document:** AQAA_PHASE1_IMPLEMENTATION_PLAN  
**Sprint:** Recovery Sprint — Phase 1  
**Date:** 2026-07-13  
**Status:** EXECUTED

---

## Objective

Replace placeholder embeddings and fix the AI intelligence layer so that:
1. `is_placeholder_mode` returns `false` in all AI assistant responses
2. Qdrant retrieval is semantically grounded (real cosine similarity)
3. The embedding provider works in both the host Python environment and the Docker container
4. No API keys are exposed; no external services are required for embeddings

---

## Execution Steps

### Step 1 — Diagnose embedding provider chain
- Read `backend/app/knowledge_indexing/embedding_service.py`
- Identify `PlaceholderEmbeddingService` as the active provider
- Identify `IS_PLACEHOLDER=True` as the root cause of `is_placeholder_mode: true`

### Step 2 — Evaluate provider options
- OpenAI: insufficient_quota → rejected
- sentence-transformers: works on host, fails in Docker (no torch) → partial
- HuggingFace API: 401 Unauthorized (auth required) → rejected
- Gemini: invalid key format → rejected
- fastembed: ONNX, no torch, works in slim container → **selected**

### Step 3 — Install fastembed
```bash
# Host
pip install fastembed --quiet

# Docker container (running)
docker exec aqaa-backend pip install fastembed --quiet
```

### Step 4 — Add FastEmbedEmbeddingService
- Added `FastEmbedEmbeddingService` class to `embedding_service.py`
- Updated factory to support `EMBEDDING_PROVIDER=fastembed`
- Updated fallback chain: fastembed → sentence_transformers → huggingface → openai → placeholder

### Step 5 — Update configuration
- `backend/.env`: `EMBEDDING_PROVIDER=fastembed`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`
- `backend/app/config.py`: updated defaults to match

### Step 6 — Add to requirements.txt
```
fastembed>=0.3,<1.0
```

### Step 7 — Reindex Qdrant collections
```bash
cd backend
python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate
```
- TUT: 196 chunks indexed with BAAI/bge-small-en-v1.5 ✓
- UP: 28 chunks indexed with BAAI/bge-small-en-v1.5 ✓

### Step 8 — Restart Docker backend
```bash
docker compose restart backend
```

### Step 9 — Verify in Docker
```bash
docker exec aqaa-backend python -c "
from app.knowledge_indexing.embedding_service import embedding_service
print(type(embedding_service).__name__, embedding_service.IS_PLACEHOLDER)
"
# → FastEmbedEmbeddingService False
```

### Step 10 — Fix stale DEV_MODE_NOTICE
- `assistant_service.py` line 182: changed from unconditional to conditional on `IS_PLACEHOLDER`

### Step 11 — End-to-end API test
```
POST /api/v1/ai-assistant/ask → is_placeholder_mode: false ✓
```

---

## Definition of Done — Phase 1

| Criterion | Status |
|-----------|--------|
| `FastEmbedEmbeddingService` implemented | ✓ |
| `fastembed` in `requirements.txt` | ✓ |
| `EMBEDDING_PROVIDER=fastembed` in `.env` | ✓ |
| Docker container uses real embeddings | ✓ |
| Qdrant collections reindexed (196 + 28 chunks) | ✓ |
| `is_placeholder_mode: false` in AI responses | ✓ |
| Stale placeholder notice removed from answers | ✓ |
| No API keys required for embeddings | ✓ |
| No torch required in Docker | ✓ |
