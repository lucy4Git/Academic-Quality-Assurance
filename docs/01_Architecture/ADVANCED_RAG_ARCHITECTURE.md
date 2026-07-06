# Advanced RAG Architecture

## Overview

Phase 3 Sprint 3 introduces an **Advanced Retrieval-Augmented Generation (RAG)** pipeline that replaces the basic `assistant_service.ask()` call in the two main AI assistant endpoints (`/ask` and `/ask-stream`). The pipeline adds source re-ranking, numbered citation injection, and citation verification.

## Pipeline Steps

```
User Question
    │
    ▼
1. Intent Classification (classify_intent)
    │
    ▼
2. Qdrant Retrieval (search_knowledge — tenant-scoped)
    │
    ▼
3. Source Ranking (source_ranker.rank_sources)
   - Cross-tenant isolation enforcement
   - Combined score: 0.7 × relevance + 0.3 × confidence
   - Entity-type boost (+0.05) for intent-matched types
    │
    ▼
4. Context Building (context_builder.build_context)
   - Numbered [SOURCE:N] blocks injected into system prompt
   - Citation index built (SOURCE:N → metadata)
    │
    ▼
5. LLM Call (build_grounded_system_prompt → provider.complete)
   - Mandatory [SOURCE:N] citation rules in system prompt
   - LOCAL_DEV: template assembly fallback
    │
    ▼
6. Citation Verification (citation_verifier.verify_citations)
   - Extracts [SOURCE:N] refs from LLM answer
   - Flags unsupported factual claims
   - Assigns grounding_status: grounded | partially_grounded | no_source_found
    │
    ▼
7. Response Assembly (advanced_ask return dict)
   + citations, unsupported_claims, grounding_status
```

## New Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| `source_ranker` | `backend/app/rag/source_ranker.py` | Re-rank Qdrant results; enforce cross-tenant isolation |
| `context_builder` | `backend/app/rag/context_builder.py` | Build numbered [SOURCE:N] prompt blocks |
| `citation_verifier` | `backend/app/rag/citation_verifier.py` | Extract citations; flag unsupported claims |
| `advanced_rag_service` | `backend/app/rag/advanced_rag_service.py` | Orchestrates full pipeline |

## SSE Event Sequence (updated)

```
start    → routing decision
token    → incremental answer words (renamed from "chunk")
sources  → Qdrant sources + follow-ups
metadata → citations, unsupported_claims, grounding_status (NEW)
done     → provider/model info
```

## Tenant Isolation

The `source_ranker` enforces cross-tenant isolation: any chunk whose `institution_code` differs from the request institution is rejected with a warning log. Chunks with an empty `institution_code` are allowed through (they are institution-agnostic).

## Backward Compatibility

- `assistant_service.ask()` is unchanged — still used by multi-agent and session endpoints.
- `AskResponse` fields `citations`, `unsupported_claims`, `grounding_status` have defaults so existing consumers continue to work.
- Frontend handles both `chunk` and `token` SSE events for graceful degradation.
