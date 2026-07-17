# AQAA Known Issues Register

**Audit Date:** 2026-07-13  
**Format:** Each issue is independently actionable with enough context to fix without this document.

---

## Issue Register

| ID | Severity | Component | Title |
|----|----------|-----------|-------|
| KI-001 | CRITICAL | Backend / Qdrant | Placeholder hash embeddings block semantic RAG |
| KI-002 | HIGH | Backend / Routes | Global audit list returns empty |
| KI-003 | HIGH | Frontend | Findings page is PlaceholderPage |
| KI-004 | HIGH | Frontend | Accreditation Readiness page is PlaceholderPage |
| KI-005 | HIGH | Backend | Knowledge search returns 405 |
| KI-006 | MEDIUM | Frontend | All settings pages are PlaceholderPage |
| KI-007 | MEDIUM | Frontend | Compliance report page is PlaceholderPage |
| KI-008 | MEDIUM | Backend | PDF export returns text, not PDF |
| KI-009 | MEDIUM | Backend | Qualification search path returns 404 |
| KI-010 | LOW | Frontend | Old `/ai-assistant` route not removed |
| KI-011 | LOW | Infrastructure | Redis usage unconfirmed |
| KI-012 | LOW | Infrastructure | MongoDB not wired |
| KI-013 | LOW | Frontend | Dean / HOD / Coordinator roles not live-tested |

---

## Detailed Descriptions

### KI-001 — Placeholder Hash Embeddings

**Severity:** CRITICAL  
**File:** `backend/app/services/` (embedding/indexing logic) + Qdrant  
**Symptom:** Every AI ask response includes `"is_placeholder_mode": true`  
**Root cause:** Documents in Qdrant are indexed with hash-based placeholder vectors, not real semantic embeddings. The embedding model was not integrated.  
**Fix:** Integrate a real embedding model into the indexing pipeline. Re-index all documents. Candidates: OpenAI `text-embedding-3-small`, Google `text-embedding-004`, or a local model via `sentence-transformers`. Update the AI assistant service to use real vector similarity.  
**Test:** After fix, `POST /api/v1/ai-assistant/ask` should return `"is_placeholder_mode": false` and citations should be semantically relevant to the question.

---

### KI-002 — Global Audit List Empty

**Severity:** HIGH  
**File:** `backend/app/routes/audits.py` — the `GET /api/v1/audits` handler  
**Symptom:** `GET /api/v1/audits` returns `{"items": [], "total": 0}` despite completed audit runs existing in the database  
**Evidence:** Per-module query `GET /api/v1/audits/modules/{id}/latest` returns correct data  
**Root cause:** Unknown — likely a broken WHERE clause, JOIN issue, or tenant scope filter in the audits list query  
**Fix:** Debug the `GET /api/v1/audits` query. Check if it filters by `module_id IS NOT NULL` incorrectly (excluding programme-scoped runs), or if a JOIN eliminates rows unexpectedly. Compare the working per-module query to identify the difference.  
**Frontend impact:** `AuditCentre.tsx` uses `useAudits()` hook → Audit Centre always shows empty list  
**Test:** After fix, `GET /api/v1/audits` should return at least 1 completed audit run.

---

### KI-003 — Findings Page Placeholder

**Severity:** HIGH  
**File:** `frontend/src/app/(main)/findings/page.tsx`  
**Symptom:** Renders `<PlaceholderPage title="Findings" />`  
**Additional:** `GET /api/v1/findings` → 404 (no backend route)  
**Fix:** 
1. Add `GET /api/v1/findings` backend route with RBAC filtering (at minimum QA_AND_ABOVE) and tenant isolation
2. Create `frontend/src/app/(main)/findings/FindingsView.tsx` with list + filters + status badges
3. Update `page.tsx` to render `<FindingsView />`

---

### KI-004 — Accreditation Readiness Page Placeholder

**Severity:** HIGH  
**File:** `frontend/src/app/(main)/accreditation/page.tsx`  
**Symptom:** Renders `<PlaceholderPage title="Accreditation Readiness" />`  
**Backend status:** `accreditation_readiness_audits.py` route complete; agent and service implemented  
**Fix:** Create `AccreditationView.tsx` that lists accreditation audit runs per institution/programme and provides a trigger UI. The backend trigger path is `POST /api/v1/accreditation-readiness-audits/modules/{id}/trigger`.

---

### KI-005 — Knowledge Search Returns 405

**Severity:** HIGH  
**File:** `backend/app/routes/` (knowledge search route)  
**Symptom:** `GET /api/v1/knowledge-search` → 405 Method Not Allowed  
**Possible causes:** (a) Route requires POST not GET, (b) Route not mounted in `main.py`, (c) Endpoint path differs  
**Fix:** Locate the knowledge search route definition. If it requires POST with body, update the frontend hook. If not mounted, add to `main.py`. If path differs, update client calls.

---

### KI-006 — Settings Pages Placeholder

**Severity:** MEDIUM  
**Files:** `frontend/src/app/(main)/settings/` (all sub-pages)  
**Symptom:** All render `<PlaceholderPage>`  
**Fix:** Implement at minimum:
- `settings/profile/` — name, email display, institution
- `settings/security/` — password change form
- `settings/notifications/` — notification preference toggles
Backend endpoints for profile update and password change need to be confirmed or created.

---

### KI-007 — Compliance Report Page Placeholder

**Severity:** MEDIUM  
**File:** `frontend/src/app/(main)/reports/compliance/page.tsx`  
**Symptom:** Renders `<PlaceholderPage>`  
**Backend:** `GET /api/v1/reporting/compliance-summary` exists  
**Fix:** Create `ComplianceReportView.tsx` that fetches `/api/v1/reporting/compliance-summary` and renders a compliance summary table/chart.

---

### KI-008 — PDF Export is Text

**Severity:** MEDIUM  
**File:** `backend/app/routes/reporting.py` — `GET /reporting/export/pdf`  
**Symptom:** Endpoint returns `text/plain` content instead of `application/pdf`  
**Fix:** Integrate a PDF generation library (e.g., `reportlab`, `weasyprint`, or `fpdf2`). Generate a real PDF from the dashboard data. Update content-type header to `application/pdf` and filename to `.pdf`.

---

### KI-009 — Qualification Search 404

**Severity:** MEDIUM  
**File:** `backend/app/routes/qualification.py`  
**Symptom:** `GET /api/v1/qualification/search` → 404  
**Fix:** Locate the correct search endpoint path in `qualification.py`. Update frontend hook or fix route mounting if necessary.

---

### KI-010 — Old `/ai-assistant` Route

**Severity:** LOW  
**File:** `frontend/src/app/(main)/ai-assistant/`  
**Symptom:** Old AI workspace page still accessible at `/ai-assistant`; not linked from anywhere in the app  
**Fix:** Remove `frontend/src/app/(main)/ai-assistant/` directory entirely. Add a redirect in `next.config.js`: `{ source: '/ai-assistant', destination: '/ai-workspace', permanent: true }`.

---

### KI-011 — Redis Usage Unconfirmed

**Severity:** LOW  
**File:** `backend/` — search for Redis client usage  
**Symptom:** Redis container running; no explicit Redis usage confirmed in audit  
**Fix:** Grep for `redis` in `backend/app/` to confirm actual usage and document it in `CLAUDE.md`.

---

### KI-012 — MongoDB Not Wired

**Severity:** LOW  
**Status:** Design-only; no code  
**Fix:** If MongoDB is needed for a specific feature (e.g., document store for large text), add the container to docker-compose and wire the connection. If MongoDB was dropped in favour of PostgreSQL, remove the reference from CLAUDE.md.

---

### KI-013 — Dean/HOD/Coordinator Not Live-Tested

**Severity:** LOW  
**Status:** RBAC code correct based on inspection; roles not exercised in browser  
**Fix:** Log in as `dean.engineering@tut.ac.za` (or equivalent seeded user) and verify: (a) sidebar shows Home, Workspace, Knowledge, Quality; (b) can trigger audits; (c) Continue Working includes Audit Centre; (d) Reports visible for Dean, hidden for HOD and below.
