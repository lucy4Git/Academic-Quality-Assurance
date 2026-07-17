# AQAA Failures and Regressions Report

**Audit Date:** 2026-07-13  
**Evidence Source:** Live API testing, browser testing, code inspection  
**Methodology:** No speculation. Each item was confirmed through a specific test or observation.

---

## CRITICAL Failures (Block core functionality)

### F-001: Placeholder Embeddings — AI Retrieval Not Semantic

**Severity:** CRITICAL  
**Category:** AI / RAG  
**Evidence:** Live API test — `POST /api/v1/ai-assistant/ask` returns `"is_placeholder_mode": true`, `"message": "hash-based placeholder embeddings, not semantic embeddings"`  
**Impact:** The RAG system generates answers using a real LLM but retrieves documents by hash proximity rather than semantic similarity. Citations are not guaranteed to be relevant to the query. The "92% grounding score" shown in the UI is LLM-self-reported confidence, not computed from retrieval quality.  
**Phase Introduced:** Qdrant was configured during Phase 2/3. Hash-based indexing was a placeholder that was never replaced.  
**Fix Required:** Implement real embedding generation (e.g., `text-embedding-3-small`, `text-embedding-004`) and re-index all documents in Qdrant.

---

### F-002: Global Audit List Always Empty

**Severity:** HIGH  
**Category:** Backend / Routing  
**Evidence:** Live API test — `GET /api/v1/audits` returns `{"items": [], "total": 0}` despite confirmed completed audit runs in the database (per-module query returns results).  
**Impact:** The AuditCentre frontend (`AuditCentre.tsx`) calls `useAudits()` which hits this endpoint. The Audit Centre will always appear empty for all users, including administrators.  
**Fix Required:** Debug the query in `audits.py` — likely a broken tenant scope filter or a JOIN producing no matches. The per-module path (`/api/v1/audits/modules/{id}/latest`) works correctly and can be used to confirm data exists.

---

## HIGH Severity Issues

### F-003: Knowledge Search Returns 405

**Severity:** HIGH  
**Category:** Backend / Routing  
**Evidence:** Live API test — `GET /api/v1/knowledge-search` → 405 Method Not Allowed  
**Impact:** Semantic knowledge search unavailable. The Knowledge Search feature card on the Knowledge landing page links to a non-functional endpoint.  
**Fix Required:** Investigate correct HTTP method for `/api/v1/knowledge-search` (may require POST with body, not GET), or check if route is not mounted.

---

### F-004: Findings Page is a Placeholder

**Severity:** HIGH  
**Category:** Frontend / Feature gap  
**Evidence:** `/findings/page.tsx` imports and renders `<PlaceholderPage title="Findings" />`  
**Impact:** No user can browse audit findings through the frontend. Findings are only accessible as embedded data within completed audit run detail views.  
**Additional:** `GET /api/v1/findings` → 404 (no dedicated findings list API route).  
**Fix Required:** Implement findings list page + backend findings list endpoint with appropriate RBAC filtering.

---

### F-005: Accreditation Readiness Page is a Placeholder

**Severity:** HIGH  
**Category:** Frontend / Feature gap  
**Evidence:** `/accreditation/page.tsx` imports and renders `<PlaceholderPage title="Accreditation Readiness" />`  
**Impact:** The Accreditation Readiness agent (`accreditation_readiness_audits.py`) is fully implemented in the backend and can be triggered, but there is no frontend to view results or initiate the accreditation workflow.

---

## MEDIUM Severity Issues

### F-006: Qualification Search Returns 404

**Severity:** MEDIUM  
**Category:** Backend / Routing  
**Evidence:** `GET /api/v1/qualification/search` → 404 during audit  
**Impact:** Qualification intelligence feature non-functional via tested path. May be a path issue (correct path may differ).

---

### F-007: All Settings Pages are Placeholders

**Severity:** MEDIUM  
**Category:** Frontend / Feature gap  
**Evidence:** `/settings/`, `/settings/profile`, `/settings/notifications`, `/settings/security`, `/settings/system` all render `<PlaceholderPage>`  
**Impact:** No user can update their profile, change notification preferences, or manage security settings. System admins cannot configure system settings via UI.

---

### F-008: Compliance Report Page is a Placeholder

**Severity:** MEDIUM  
**Category:** Frontend / Feature gap  
**Evidence:** `/reports/compliance/page.tsx` renders `<PlaceholderPage>`  
**Impact:** Compliance reporting is the primary deliverable for QA officers. The reporting backend exists (`GET /api/v1/reporting/compliance-summary`) but the frontend page is not implemented.

---

### F-009: PDF Export is Text-Only Placeholder

**Severity:** MEDIUM  
**Category:** Backend / Feature gap  
**Evidence:** `GET /api/v1/reporting/export/pdf` returns `text/plain` content  
**Impact:** PDF export in the ReportsView sends data but receives a text file renamed `.txt`. Not a true PDF.

---

## LOW Severity Issues

### F-010: Old `/ai-assistant` Route Not Removed

**Severity:** LOW  
**Category:** Technical Debt  
**Evidence:** Directory `frontend/src/app/(main)/ai-assistant/` still exists; all links updated to `/ai-workspace` in Phase 4 Wave 2  
**Impact:** If a user navigates directly to `/ai-assistant`, they reach the old UI. No in-app link points there anymore.

---

### F-011: Redis Role Unconfirmed

**Severity:** LOW  
**Category:** Infrastructure / Unknown  
**Evidence:** Redis container runs; no explicit Redis usage confirmed in code review  
**Impact:** Unknown. If Redis is used for session management or rate limiting and goes down, unknown failure modes.

---

### F-012: MongoDB Not Wired

**Severity:** LOW  
**Category:** Architecture / Not Started  
**Evidence:** CLAUDE.md: "MongoDB (architected, not yet wired)". No MongoDB container in docker-compose.  
**Impact:** Any features planned for MongoDB are not available. Not a current blocker.

---

## Regressions Introduced During Audited Period

| Phase | Regression | Status |
|-------|-----------|--------|
| Phase 2 S3 | 3-panel AI workspace became obsolete in Phase 4 W2 | Resolved — replaced cleanly |
| Phase 4 W1 | `FloatingAIButton` removed (was in Phase 2/3 shell) | Resolved — replaced by Home + Workspace composers |
| Phase 4 W3 | Lecturer `/audits` link in Continue Working | **Fixed within the same sprint** |
| Phase 4 W3 | `AskAQAAComposer` hidden from students | **Fixed within the same sprint** |
| Phase 4 W3 | Prompts linking to old `/ai-assistant` | **Fixed within the same sprint** |

**Assessment:** No outstanding regressions from Phase 4 work. All regressions introduced during Wave 3 were identified and fixed within the same sprint.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 (placeholder embeddings, empty audit list) |
| HIGH | 3 (knowledge search 405, findings placeholder, accreditation placeholder) |
| MEDIUM | 4 (qualification 404, all settings placeholder, compliance placeholder, PDF text-only) |
| LOW | 3 (old route, Redis unknown, MongoDB not wired) |
| **Total** | **12** |
