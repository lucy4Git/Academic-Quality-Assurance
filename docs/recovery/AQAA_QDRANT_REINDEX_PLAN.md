# AQAA Qdrant Reindex Plan

**Document:** AQAA_QDRANT_REINDEX_PLAN  
**Sprint:** Recovery Sprint — Phase 1  
**Date:** 2026-07-13  
**Status:** EXECUTED AND VERIFIED

---

## Collections Reindexed

| Collection name | Institution | IKP version | Chunks | Dimensions | Model |
|----------------|-------------|-------------|--------|------------|-------|
| `tut_2026_v1_1_0` | TUT (Tshwane University of Technology) | v1.1.0 | 196 | 384 | BAAI/bge-small-en-v1.5 |
| `up_2026_v1_0_0` | UP (University of Pretoria) | v1.0.0 | 28 | 384 | BAAI/bge-small-en-v1.5 |

---

## Reindex Command

```bash
# From repo root (host Python, not Docker)
cd backend
python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate
```

`--force-recreate` deletes and recreates each collection. Required when switching embedding providers or when vectors are stale (e.g., previously indexed with placeholder SHA-256 embeddings).

---

## When to Re-run

Reindex is required when:
- `EMBEDDING_PROVIDER` changes (different model, different library)
- `EMBEDDING_MODEL` changes (different model within same library)
- Dimensions change (must match at index time and query time)
- New IKP versions are added for an institution
- `knowledge_chunks.json` source files are updated

Reindex is NOT required for:
- Backend code changes that do not touch the embedding pipeline
- Frontend changes
- AI provider changes (OpenAI, Anthropic, etc.)
- RBAC or auth changes

---

## Intermediate Indexing History

| Date | Provider | Model | Dims | Result |
|------|----------|-------|------|--------|
| Recovery Sprint Day 1 | sentence_transformers (host only) | all-MiniLM-L6-v2 | 384 | TUT: 196 chunks, UP: 28 chunks — but Docker had no torch, so query-time fell back to placeholder |
| Recovery Sprint Day 1 | fastembed (host + Docker) | BAAI/bge-small-en-v1.5 | 384 | TUT: 196 chunks, UP: 28 chunks — both host and Docker use same model → consistent |

---

## Source Chunk Files

```
ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json   → 196 chunks
ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json    → 28 chunks
```

These are the Academic Intelligence Layer source files for each institution. They contain structured chunks of institutional knowledge (modules, programmes, policies, staff) used for RAG-based AI answers.

---

## Collection Naming Convention

```
{institution_code}_{year}_{version_safe}

Examples:
  tut_2026_v1_1_0   (TUT, 2026, v1.1.0)
  up_2026_v1_0_0    (UP, 2026, v1.0.0)
```

The `qdrant_service.py` derives the collection name from the IKP metadata. The version string dots are replaced with underscores.

---

## Verification After Reindex

```bash
# Check collection counts
curl http://localhost:6333/collections

# Check point count in a collection
curl http://localhost:6333/collections/tut_2026_v1_1_0

# Test query via AI assistant
POST /api/v1/ai-assistant/ask
{
  "question": "What are the assessment requirements for TUT modules?",
  "institution_code": "tut",
  "ikp_version": "v1.1.0"
}
# Expect: is_placeholder_mode: false, sources with semantically relevant chunks
```
