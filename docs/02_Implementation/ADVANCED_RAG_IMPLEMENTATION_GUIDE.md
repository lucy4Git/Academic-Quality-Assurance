# Advanced RAG Implementation Guide

## Quick Start

The Advanced RAG pipeline is enabled by default. No configuration changes are required. When `AI_PROVIDER=local_dev` (default), template-based answers are returned with citation verification applied to the template output.

## Key Files

```
backend/app/rag/
├── __init__.py
├── source_ranker.py          # Re-rank + cross-tenant guard
├── context_builder.py        # [SOURCE:N] block builder
├── citation_verifier.py      # Citation extraction + grounding
└── advanced_rag_service.py   # Orchestrator

backend/app/ai_assistant/
└── prompt_templates.py       # build_grounded_system_prompt() added

backend/app/schemas/
└── ai_assistant.py           # Citation model + AskResponse extended

backend/app/routes/
└── ai_assistant.py           # /ask and /ask-stream updated
```

## How Citations Work

1. `build_context()` numbers each Qdrant chunk: `[SOURCE:1]`, `[SOURCE:2]`, etc.
2. `build_grounded_system_prompt()` injects mandatory citation rules into the system prompt.
3. The LLM writes `[SOURCE:N]` inline in its answer.
4. `verify_citations()` extracts all `[SOURCE:N]` refs and cross-references the citation index.
5. Unresolved source numbers (e.g., `[SOURCE:5]` when only 3 sources exist) are silently dropped from the citations list.

## Grounding Status Rules

| Status | Condition |
|--------|-----------|
| `grounded` | Citations present AND no unsupported factual claims |
| `partially_grounded` | Citations present but some unsupported claims, OR no citations in answer but sources were retrieved |
| `no_source_found` | Citation index is empty (no sources retrieved) |

## Adding a New Entity Boost

In `source_ranker.py`, add to `_ENTITY_BOOST`:

```python
"new_intent": "entity_type_to_boost",
```

The boost value is `_BOOST_VALUE = 0.05`. Increase it if you need stronger re-ranking.

## Running the RAG Tests

```bash
cd backend
python -m pytest tests/test_p3s3_advanced_rag.py -v
python -m pytest tests/test_p3s3_streaming_metadata.py -v
```
