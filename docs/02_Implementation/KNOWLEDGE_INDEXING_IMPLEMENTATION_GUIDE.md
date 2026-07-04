# Knowledge Indexing Implementation Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Sprint:** Sprint 2 — Qdrant Vector Indexing  
**Status:** Implemented

---

## Overview

The Knowledge Indexing subsystem loads IKP AI-ready knowledge chunks from JSON
files into Qdrant collections, enabling semantic search over institutional
knowledge from the frontend and from AI audit agents.

---

## Architecture

```
ikp/institutions/{code}/{year}/{version}/ai/knowledge_chunks.json
                    │
                    ▼
    index_ikp_chunks.py        (CLI + library)
         ├── loads JSON chunks
         ├── normalises to canonical payload
         ├── calls EmbeddingService.embed_texts()
         └── calls QdrantService.upsert_points()
                    │
                    ▼
    Qdrant collection: {code}_{year}_{version}
    e.g. tut_2026_v1_1_0  / up_2026_v1_0_0
                    │
                    ▼
    search_service.py           (tenant-isolated search)
                    │
                    ▼
    routes/knowledge_index.py   (FastAPI endpoints)
                    │
                    ▼
    /api/proxy/knowledge-search (Next.js → FastAPI proxy)
                    │
                    ▼
    KnowledgeSearchView.tsx     (/knowledge-search page)
```

---

## Module Locations

| File | Purpose |
|---|---|
| `backend/app/knowledge_indexing/__init__.py` | Package docstring |
| `backend/app/knowledge_indexing/embedding_service.py` | Text → vector (dev placeholder) |
| `backend/app/knowledge_indexing/qdrant_service.py` | Qdrant collection + point management |
| `backend/app/knowledge_indexing/index_ikp_chunks.py` | CLI + indexing library |
| `backend/app/knowledge_indexing/search_service.py` | Semantic search with tenant isolation |
| `backend/app/schemas/knowledge_index.py` | Pydantic request/response schemas |
| `backend/app/routes/knowledge_index.py` | FastAPI route handlers |
| `frontend/src/hooks/useKnowledgeSearch.ts` | TanStack Query hooks |
| `frontend/src/types/knowledge-index.ts` | TypeScript types |
| `frontend/src/app/(main)/knowledge-search/` | Search page and view |

---

## Collection Naming

```
{institution_code_lower}_{academic_year}_{version_with_underscores}

Examples:
  TUT 2026 v1.1.0  →  tut_2026_v1_1_0
  UP  2026 v1.0.0  →  up_2026_v1_0_0
```

Dots in version strings are replaced with underscores to produce a valid
Qdrant collection identifier.

---

## Canonical Payload Schema

Every vector point in Qdrant carries this payload:

```json
{
  "institution_code":  "TUT",
  "institution_id":    "UUID or empty string",
  "ikp_version":       "v1.1.0",
  "academic_year":     "2026",
  "entity_type":       "programme",
  "entity_id":         "tut-prog-001",
  "title":             "Diploma In Computer Science",
  "text":              "Programme: Diploma In Computer Science. NQF Level: 6...",
  "source_document":   "ea19be11-8749-417d-8e62-7ea3540ae470",
  "provenance_id":     "tut-prog-001",
  "confidence_score":  0.92
}
```

---

## Chunk Format Normalisation

TUT chunks use `entity_type`; UP chunks use `chunk_type`. The normalisation
function `_normalize_chunk()` in `index_ikp_chunks.py` handles both:

```python
entity_type = raw.get("entity_type") or raw.get("chunk_type") or "unknown"
source_document = str(metadata.get("source") or metadata.get("source_id") or "")
```

---

## Embedding Service

**Current:** Development placeholder — 384-dim deterministic vectors from
iterative SHA-256 hashing. Vectors are unit-normalised. No NaN/Inf values.

**To replace with real embeddings:**

1. Open `backend/app/knowledge_indexing/embedding_service.py`
2. Replace the `EmbeddingService` class body with a real model:
   ```python
   from sentence_transformers import SentenceTransformer
   
   class EmbeddingService:
       DIMENSIONS = 384
       IS_PLACEHOLDER = False
       MODEL_NAME = "all-MiniLM-L6-v2"
       
       def __init__(self):
           self._model = SentenceTransformer("all-MiniLM-L6-v2")
       
       def embed_texts(self, texts: list[str]) -> list[list[float]]:
           return self._model.encode(texts, normalize_embeddings=True).tolist()
       
       def embed_query(self, query: str) -> list[float]:
           return self.embed_texts([query])[0]
   ```
3. If dimensions change (e.g. 768 for `all-mpnet-base-v2`):
   - Update `EMBEDDING_DIMENSIONS` constant
   - Run `--force-recreate` to rebuild Qdrant collections
4. Add `sentence-transformers` to `requirements.txt`

The interface (`embed_texts`, `embed_query`, `DIMENSIONS`, `IS_PLACEHOLDER`,
`MODEL_NAME`) is stable — no other code changes required.

---

## Tenant Isolation

Isolation is enforced at three layers:

| Layer | Mechanism |
|---|---|
| Collection | One Qdrant collection per institution — no cross-collection reads |
| Search service | `ACTIVE_INSTITUTION_CODES` registry blocks GFU/RCT |
| Route handler | Non-admin: `institution_code` verified against user's institution; archived institutions return 403 |

System Admin is the only role that can specify any active pilot institution in
the search request. All other roles must search their own institution.

---

## API Endpoints

### POST /api/v1/knowledge-index/index

Trigger indexing of one institution's IKP chunks. Admin only.

```json
Request:  { "institution_code": "TUT", "academic_year": "2026", "ikp_version": "v1.1.0", "force_recreate": false }
Response: { "collection": "tut_2026_v1_1_0", "chunks_indexed": 196, "status": "ok", "message": "..." }
```

### GET /api/v1/knowledge-index/status

Collection status for all registered pilot institutions. QA Officer+.

### POST /api/v1/knowledge-search

Semantic search. Lecturer+.

```json
Request:  { "query": "NQF level 6 computer science", "institution_code": "TUT", "entity_type": "programme", "top_k": 10 }
Response: { "query": "...", "institution_code": "TUT", "total_results": N, "results": [...] }
```

---

## Adding a New Institution

1. Add chunk file: `ikp/institutions/{code}/{year}/{version}/ai/knowledge_chunks.json`
2. Add to `PILOT_INSTITUTIONS` in `index_ikp_chunks.py`
3. Add to `ACTIVE_PILOT_COLLECTIONS` in `search_service.py`
4. Run: `python -m app.knowledge_indexing.index_ikp_chunks --institution {CODE}`
5. Update `PILOT_DATA_MANAGEMENT_GUIDE.md`
