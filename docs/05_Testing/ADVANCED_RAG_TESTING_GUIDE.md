# Advanced RAG Testing Guide

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_p3s3_advanced_rag.py` | 26 | SourceRanker, ContextBuilder, CitationVerifier, AdvancedRagService |
| `test_p3s3_streaming_metadata.py` | 14 | Token events, Metadata event, RBAC |

## Running Tests

```bash
cd backend
python -m pytest tests/test_p3s3_advanced_rag.py -v
python -m pytest tests/test_p3s3_streaming_metadata.py -v
python -m pytest -q   # full suite — must be 1091+ passing
```

## Test Coverage by Module

### SourceRanker (8 tests)
- Empty input → empty output
- Cross-tenant chunk rejection
- Score-based ranking order
- Entity-type boost for matching intent
- Score clamping to 1.0
- Empty institution_code accepted
- Unknown intent does not raise

### ContextBuilder (6 tests)
- Empty input → no-source message + empty index
- Single chunk → SOURCE:1 key
- Multiple chunks → sequential numbering
- Citation index structure (all required fields)
- Snippet truncated at 200 chars

### CitationVerifier (8 tests)
- No sources → `no_source_found`
- Clean citation → `grounded`
- Unsupported factual claim flagged
- Unresolved source number dropped
- Meta-prefixed sentence not flagged
- Short sentence (<20 chars) not flagged
- Mixed citations → `partially_grounded`
- No [SOURCE:N] in answer → `partially_grounded`

### AdvancedRagService (4 tests)
- Full pipeline returns `grounding_status`
- Full pipeline returns `citations` list
- Cross-tenant chunk excluded from sources
- No sources → `no_source_found`

### Streaming (11 tests)
- `token` event type emitted (not `chunk`)
- `token` events have `content` field
- Multiple token events for long answers
- `sources` event still present
- `done` event still present
- `metadata` event present
- `metadata` has `citations`, `unsupported_claims`, `grounding_status`
- Grounding status is a valid enum value
- `metadata` comes after `sources`
- RBAC: student role not in allowed set
- Error event on provider failure

## Mock Strategy

All tests use `unittest.mock` — no real database, Qdrant, or AI provider connections. The `search_knowledge` function is patched to return controlled chunk lists. The AI provider is mocked with `is_local_dev=True` to exercise the template-assembly path.
