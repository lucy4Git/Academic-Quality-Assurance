# AQAA Security and Tenant Validation

**Document:** AQAA_SECURITY_AND_TENANT_VALIDATION  
**Sprint:** Recovery Sprint  
**Date:** 2026-07-13  
**Status:** ARCHITECTURE CONFIRMED — RUNTIME TEST PENDING

---

## Security Architecture — Confirmed Unchanged

The following security controls were audited during the Recovery Sprint. None were modified.

### JWT Authentication
- Tokens are HS256, signed with `SECRET_KEY`
- Access tokens: 60 min expiry
- Refresh tokens: 7 days expiry
- Tokens stored in `httpOnly` cookies only — inaccessible to JavaScript
- Token validation: `get_current_user` dependency in `backend/app/dependencies.py`

### API Proxy Pattern
- Browser JavaScript never calls FastAPI directly
- All API calls go through `/api/proxy/{path}` (Next.js route handler)
- Proxy reads `access_token` cookie server-side and adds `Authorization: Bearer` header
- The cookie's `httpOnly` attribute prevents XSS from reading tokens

### RBAC (Role-Based Access Control)
- Hierarchy: `system_admin → quality_assurance_officer → faculty_dean → head_of_department → programme_coordinator → lecturer → student`
- Role shortcuts (`AdminRequired`, `QAOfficerRequired`, etc.) are FastAPI `Depends` objects
- Never bypassed, never double-wrapped, never replaced with admin shortcuts during recovery

### Tenant Isolation
- All user-scoped queries filter by `institution_id` (FK on User model)
- Qdrant searches filter by `institution_code` metadata field
- AI assistant validates `institution_code` against the calling user's institution before any search
- Cross-institution data access is architecturally impossible at the query layer

---

## What Was NOT Done During Recovery (Security Constraints Honoured)

| Rule | Adherence |
|------|-----------|
| Do not expose API keys | ✓ No keys logged, printed, or returned in error messages |
| Do not remove tenant filters | ✓ All `institution_id` and `institution_code` filters untouched |
| Do not disable RBAC | ✓ All role dependencies preserved |
| Do not use admin bypasses | ✓ No bypass routes added |
| Do not log document contents | ✓ Only metadata logged |
| Do not log access tokens | ✓ Tokens never appear in logs |
| Do not return evidence to system admins automatically | ✓ Agent outputs scope-restricted |
| Do not add public Qdrant access | ✓ Qdrant on localhost only, no public exposure |
| Do not store secrets in frontend code | ✓ No secrets in any frontend file |
| Do not include sensitive source text in error messages | ✓ Error messages contain only metadata |

---

## Embedding Provider — Security Notes

The `fastembed` library:
- Downloads ONNX model weights from HuggingFace Hub on first use (~45 MB)
- Caches to `~/.cache/fastembed` (host) or `/root/.cache/fastembed` (Docker container)
- Requires no API key
- Makes no runtime network calls during embedding (pure local ONNX inference)
- Model weights are open-source (BAAI/bge-small-en-v1.5, Apache 2.0 licence)

The initial model download uses HuggingFace Hub (unauthenticated). This is acceptable for open-source models. Production deployments should pre-bundle the model weights or use a private model registry.

---

## Tenant Isolation — Qdrant Layer

Each Qdrant search includes an institution filter:

```python
# backend/app/knowledge_indexing/search_service.py (pattern)
filter = Filter(
    must=[FieldCondition(key="institution_code", match=MatchValue(value=institution_code))]
)
```

This means:
- A TUT user querying with `institution_code=tut` only retrieves TUT knowledge chunks
- Even if a TUT user somehow obtained a UP `institution_code`, the collection `up_2026_v1_0_0` is only accessible through the API which validates `institution_code` against the user's `institution_id`
- There is no direct Qdrant access from the frontend

---

## Recovery Changes Audit

All changes made during the Recovery Sprint are listed below with security impact assessment:

| File | Change | Security Impact |
|------|--------|----------------|
| `backend/app/main.py` | `module_audits_router` prefix changed to `/module-folder` | None — no auth or RBAC change |
| `backend/app/knowledge_indexing/embedding_service.py` | Added `FastEmbedEmbeddingService`, updated factory | None — local ONNX model, no external calls |
| `backend/app/config.py` | Updated `EMBEDDING_PROVIDER` default | None |
| `backend/.env` | Changed `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `AI_PROVIDER` | Low — `AI_PROVIDER=OPENAI` activates real LLM when key funded |
| `backend/requirements.txt` | Added `fastembed` | Low — trusted open-source library from Qdrant |
| `backend/app/ai_assistant/assistant_service.py` | Conditional `DEV_MODE_NOTICE` | None |
| `frontend/src/lib/api/moduleAudits.ts` | Updated API paths | None |
| `frontend/src/types/auditRun.ts` | New type definitions | None |
| `frontend/src/lib/api/auditRuns.ts` | New API client | None |
| `frontend/src/hooks/useAuditRuns.ts` | New hooks | None |
| `frontend/src/app/(main)/audits/AuditCentre.tsx` | Rewired to `AuditRun` | None — uses existing auth proxy |
| `frontend/src/app/(main)/audits/[id]/AuditDetailView.tsx` | Rewired to `AuditRun` | None |
