# AQAA Current Retrieval Pipeline

**Document:** AQAA_CURRENT_RETRIEVAL_PIPELINE  
**Sprint:** Recovery Sprint — Phase 1  
**Date:** 2026-07-13  
**Status:** POST-RECOVERY (REAL SEMANTIC RETRIEVAL ACTIVE)

---

## Pipeline Overview

```
User question
     │
     ▼
Intent Classification
(backend/app/ai_assistant/assistant_service.py → classify_intent)
     │ intent: programme_query | module_query | compliance_query | general
     ▼
Embed Query
(embedding_service.embed_query → FastEmbedEmbeddingService → BAAI/bge-small-en-v1.5)
     │ 384-dim float vector
     ▼
Qdrant Nearest Neighbour Search
(search_service.search_knowledge → qdrant_service.search)
     │ collection: {institution_code}_{year}_{version_safe}
     │ top_k: 5 (default, configurable)
     │ filter: institution_code (tenant isolation)
     ▼
Chunk Re-ranking
(confidence_score = cosine similarity × intent_boost)
     │ relevance_score = raw cosine similarity
     ▼
Answer Generation
     ├─ if AI_PROVIDER != LOCAL_DEV:
     │       build_system_prompt(chunks) → LLM call → real answer
     └─ if AI_PROVIDER == LOCAL_DEV (fallback):
             assemble_answer(chunks) → template answer
     │
     ▼
Response Assembly
{
  question, answer, sources[], confidence_score,
  institution_code, is_placeholder_mode,
  suggested_followups, query_mode, provider, model,
  mode, session_id, citations, unsupported_claims,
  grounding_status
}
```

---

## Component Details

### Embedding Service
- **Class:** `FastEmbedEmbeddingService`
- **Model:** `BAAI/bge-small-en-v1.5` (384 dims)
- **Library:** `fastembed>=0.3` (ONNX, no PyTorch)
- **Location:** `backend/app/knowledge_indexing/embedding_service.py`
- **Singleton:** Module-level `embedding_service` imported by `search_service.py`

### Search Service
- **File:** `backend/app/knowledge_indexing/search_service.py`
- **Function:** `search_knowledge(query, institution_code, top_k, intent)`
- **Tenant isolation:** Qdrant filter on `institution_code` metadata field
- **Collection resolution:** `{institution_code.lower()}_{year}_{version_safe}`

### Qdrant Service
- **File:** `backend/app/knowledge_indexing/qdrant_service.py`
- **Client:** `QdrantClient` (REST, `http://localhost:6333` or `http://qdrant:6333` in Docker)
- **Metric:** Cosine similarity
- **Index type:** HNSW (Qdrant default)

### Intent Classifier
- **Function:** `classify_intent(question: str) → str`
- **Method:** Keyword matching against `_INTENT_KEYWORDS` dict
- **Intents:** `programme_query`, `module_query`, `compliance_query`, `general`
- **Purpose:** Selects appropriate answer preamble and follow-up suggestions

### AI Provider (Current: LOCAL_DEV fallback)
- **Config:** `AI_PROVIDER=OPENAI` in `.env`
- **Runtime:** Falls back to `LocalDevProvider` (OpenAI quota exceeded)
- **Template file:** `backend/app/ai_assistant/prompt_templates.py`
- **Real LLM path:** Available for OpenAI, Anthropic, Ollama, Gemini when configured

---

## Tenant Isolation

Each Qdrant search is scoped by `institution_code`. The `search_knowledge` function resolves the collection name from the institution code and filters results to that institution's knowledge chunks. Cross-institution retrieval is architecturally impossible at the vector search layer.

---

## Grounding Scores

| Field | Meaning |
|-------|---------|
| `confidence_score` | Average cosine similarity across all retrieved chunks (0.0–1.0) |
| `relevance_score` | Per-source cosine similarity score |
| `grounding_status` | `grounded` (>0.8), `partially_grounded` (0.5–0.8), `ungrounded` (<0.5) |

**Pre-recovery:** All scores were derived from SHA-256 hash vectors — semantically meaningless. Scores appeared high (~0.76) due to hash distribution, not semantic match.

**Post-recovery:** Scores are cosine similarity over real BAAI/bge-small-en-v1.5 semantic vectors. A score of 0.76 now genuinely indicates moderate semantic relevance.

---

## Known Limitation

The IKP knowledge chunks (`knowledge_chunks.json`) contain structured module/programme metadata (codes, credits, names) but limited free-text policy content. Assessment compliance policy text is not currently represented as dense semantic chunks — queries about "assessment compliance requirements" retrieve module entries rather than policy documents. This is a knowledge base coverage gap, not a retrieval system defect.
