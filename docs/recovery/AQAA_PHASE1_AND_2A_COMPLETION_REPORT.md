# AQAA Phase 1 and 2A Completion Report

**Document:** AQAA_PHASE1_AND_2A_COMPLETION_REPORT  
**Sprint:** Recovery Sprint  
**Date:** 2026-07-13  
**Status:** PHASES COMPLETE

---

## Executive Summary

The Recovery Sprint successfully resolved two critical defects in the AQAA platform:

1. **Phase 1 — Semantic Retrieval Recovery:** Placeholder SHA-256 hash embeddings replaced with real BAAI/bge-small-en-v1.5 semantic embeddings via `fastembed`. `is_placeholder_mode` is now `false` in all AI assistant responses.

2. **Phase 2A — Global Audit Centre Repair:** FastAPI route registration collision causing `GET /api/v1/audits` to return empty results was identified and fixed. The Global Audit Centre now displays all 40+ completed AI audit runs.

No security controls were weakened. No RBAC was bypassed. No tenant isolation was removed. The platform architecture was preserved exactly.

---

## Phase 1 — Semantic Retrieval Recovery

### What Changed

| Component | Before | After |
|-----------|--------|-------|
| `EMBEDDING_PROVIDER` | `huggingface` (failing 401) | `fastembed` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | `BAAI/bge-small-en-v1.5` |
| Active class | `PlaceholderEmbeddingService` | `FastEmbedEmbeddingService` |
| `IS_PLACEHOLDER` | `True` | `False` |
| `is_placeholder_mode` (response) | `true` | `false` |
| Vector semantics | None (SHA-256 hash) | Real cosine similarity |
| Docker compatibility | Broken (needed torch) | Working (ONNX, no torch) |
| Stale "placeholder" notice in answers | Always shown | Suppressed |

### Files Modified

- `backend/app/knowledge_indexing/embedding_service.py` — new `FastEmbedEmbeddingService`, updated factory
- `backend/app/config.py` — updated defaults
- `backend/.env` — updated `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL`
- `backend/requirements.txt` — added `fastembed>=0.3,<1.0`
- `backend/app/ai_assistant/assistant_service.py` — conditional DEV_MODE_NOTICE

### Qdrant Collections Post-Recovery

| Collection | Chunks | Model | Dims |
|------------|--------|-------|------|
| `tut_2026_v1_1_0` | 196 | BAAI/bge-small-en-v1.5 | 384 |
| `up_2026_v1_0_0` | 28 | BAAI/bge-small-en-v1.5 | 384 |

---

## Phase 2A — Global Audit Centre Repair

### What Changed

| Component | Before | After |
|-----------|--------|-------|
| `GET /api/v1/audits` | Returned `ModuleAudit[]` (always empty) | Returns `AuditRunBrief[]` (40+ results) |
| `module_audits_router` prefix | `/api/v1` (collided) | `/api/v1/module-folder` |
| Frontend data source | `ModuleAudit` (manual checklist) | `AuditRun` (AI agent run) |
| Audit Centre state | Always empty | Shows all AI audit runs |

### Files Modified (Backend)

- `backend/app/main.py` — changed `module_audits_router` prefix

### Files Created/Modified (Frontend)

- `frontend/src/types/auditRun.ts` — new TypeScript types for `AuditRunBrief`, `AuditRunRead`, `AuditFindingRead`
- `frontend/src/types/index.ts` — added export for `auditRun`
- `frontend/src/lib/api/auditRuns.ts` — API client for audit run endpoints
- `frontend/src/hooks/useAuditRuns.ts` — TanStack Query hooks
- `frontend/src/lib/api/moduleAudits.ts` — updated paths to `/module-folder/audits/*`
- `frontend/src/app/(main)/audits/AuditCentre.tsx` — rewired to `AuditRun` data
- `frontend/src/app/(main)/audits/[id]/AuditDetailView.tsx` — rewired to `AuditRun` detail

---

## Remaining Work

### AI Provider (LLM Generation)
- `AI_PROVIDER=OPENAI` is set but the key has `insufficient_quota`
- The platform falls back to LOCAL_DEV template assembly for answer generation
- Embeddings and retrieval are real; only the LLM generation step is templated
- Resolution: fund the OpenAI key, or configure Anthropic / Ollama

### Documentation
- 12 recovery documents being written in `docs/recovery/`

### Browser Validation
- Full role-based browser test suite pending (QA officer, lecturer, coordinator, cross-tenant)
