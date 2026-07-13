# AQAA Browser Validation Report

**Document:** AQAA_BROWSER_VALIDATION_REPORT  
**Sprint:** Recovery Sprint  
**Date:** 2026-07-13  
**Status:** API VALIDATED — FULL BROWSER TEST PENDING

---

## API-Level Validation (Completed)

The following endpoints were validated via PowerShell HTTP calls against `http://localhost:8000` during the Recovery Sprint.

### Authentication

| Test | Endpoint | Result |
|------|----------|--------|
| QA officer login | `POST /api/v1/auth/login` `qa.officer@tut.ac.za` | ✓ JWT issued |
| Token used in subsequent requests | `Authorization: Bearer {token}` | ✓ All protected endpoints accessible |

### Global Audit Centre (Phase 2A)

| Test | Endpoint | Result |
|------|----------|--------|
| List audit runs | `GET /api/v1/audits` | ✓ Returns `AuditRunBrief[]` with 40+ records |
| Get audit run detail | `GET /api/v1/audits/{id}` | ✓ Returns `AuditRunRead` with findings |

### AI Assistant (Phase 1)

| Test | Endpoint | Result |
|------|----------|--------|
| Ask question | `POST /api/v1/ai-assistant/ask` | ✓ `is_placeholder_mode: false` |
| Confidence score | Response field | ✓ Real cosine similarity (not hash artifact) |
| Sources returned | Response `sources[]` | ✓ Real semantic chunks retrieved |
| Stale notice absent | Response `answer` | ✓ No "hash-based placeholder embeddings" text |
| Institution scoping | `institution_code: tut` | ✓ Only TUT chunks returned |

### Embedding Service (Docker)

| Test | Method | Result |
|------|--------|--------|
| Provider class | `docker exec aqaa-backend python -c "..."` | ✓ `FastEmbedEmbeddingService` |
| `IS_PLACEHOLDER` | Same | ✓ `False` |
| Dimensions | Same | ✓ 384 |

---

## Browser Validation (Pending)

The following full-role browser validation sessions are planned. Each requires the frontend dev server (`npm run dev` on port 3000) and Docker stack running.

### Session 1 — QA Officer Full Workflow (qa.officer@tut.ac.za)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login at `/login` | Redirect to dashboard |
| 2 | Navigate to Audit Centre | `AuditRun` list visible, 40+ entries |
| 3 | Click completed audit run | Detail view with findings and compliance score |
| 4 | Navigate to AI Workspace | Chat interface loads |
| 5 | Ask compliance question | Answer returned, `is_placeholder_mode` absent from UI |
| 6 | Check sources panel | Real chunk citations shown |

### Session 2 — Lecturer Workspace (lecturer.cs@tut.ac.za)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login at `/login` | Redirect to dashboard |
| 2 | Navigate to AI Workspace | Chat interface loads |
| 3 | Ask module-level question | Answer returned with module context |
| 4 | Navigate to Audit Centre | Lecturer's permitted runs visible |
| 5 | Attempt admin action | 403 Forbidden (RBAC enforced) |

### Session 3 — Coordinator Audit Trigger (coordinator.it@tut.ac.za)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login at `/login` | Redirect to dashboard |
| 2 | Navigate to a module | Module detail page loads |
| 3 | Trigger audit | `POST /audits/modules/{id}/trigger` → 202 |
| 4 | Poll audit status | Status transitions: pending → running → completed |
| 5 | View results in Audit Centre | New run appears in list |

### Session 4 — Cross-Tenant Isolation (qa.officer@tut.ac.za vs UP data)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login as TUT QA officer | |
| 2 | Query AI assistant with `institution_code: up` | 403 Forbidden or empty results |
| 3 | Attempt to access UP audit runs | Only TUT runs visible |
| 4 | Verify Qdrant filter | Only `tut_2026_v1_1_0` collection queried |

---

## Known Limitations

- Full browser sessions not yet conducted (requires interactive browser session)
- AI answers are LOCAL_DEV template assembly (real LLM pending — see `AQAA_PLACEHOLDER_AI_REMOVAL_REGISTER.md`)
- Semantic retrieval quality is limited by IKP chunk coverage (policy text not yet chunked — see `AQAA_RETRIEVAL_EVALUATION_REPORT.md`)
