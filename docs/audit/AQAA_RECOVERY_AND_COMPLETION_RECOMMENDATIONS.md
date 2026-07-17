# AQAA Recovery and Completion Recommendations

**Audit Date:** 2026-07-13  
**Based on:** All 14 preceding audit documents  
**Principle:** Fix critical failures before adding new features. Address broken core promises before building new UI.

---

## Priority Classification

- **P0 — Critical Path**: Blocks the platform's core value proposition
- **P1 — High Value**: Major user-facing gaps that impede primary workflows
- **P2 — Medium**: Secondary features or quality of life
- **P3 — Low**: Cleanup, polish, and nice-to-haves

---

## P0: Fix Before Any New Work

### P0.1 — Implement Real Semantic Embeddings (KI-001)

**Why P0:** The platform's headline feature — "AI-powered academic quality assurance with knowledge-grounded responses" — is currently producing answers without semantic retrieval. This is the most important broken thing in the system.

**What to do:**
1. Choose an embedding model: OpenAI `text-embedding-3-small` (1536 dims, cheap), Google `text-embedding-004`, or a free local model via `sentence-transformers` (`all-MiniLM-L6-v2`)
2. Update the document indexing service to generate real embeddings when storing documents in Qdrant
3. Re-index all existing documents
4. Update the AI assistant service to use real cosine similarity search
5. Remove the `is_placeholder_mode` flag from responses

**Test:** Ask a specific question about a known document. The returned citation should be the document containing the answer, not a random document.

**Estimated impact:** Transforms the AI from a "smart chatbot that happens to have documents nearby" into a genuine RAG system.

---

### P0.2 — Fix Global Audit List (KI-002)

**Why P0:** The Audit Centre is the primary workflow for QA officers and coordinators. It currently shows nothing.

**What to do:**
1. Open `backend/app/routes/audits.py`
2. Find the `GET /api/v1/audits` list handler
3. Compare its SQL query against the working `GET /api/v1/audits/modules/{id}/latest` query
4. The bug is likely a broken WHERE clause, a JOIN that eliminates rows, or a tenant scope filter that's too restrictive
5. Fix the query. If the global list should show all runs for the user's institution, ensure the tenant filter matches the per-module filter logic

**Test:** After login as admin, `GET /api/v1/audits` should return the completed audit run from the module trigger test.

---

## P1: High-Value Feature Completion

### P1.1 — Implement Findings Page (KI-003)

**Why P1:** Findings are the output of the entire audit pipeline. Without a findings list, QA officers cannot act on audit results without knowing individual module IDs.

**Backend:**
- Add `GET /api/v1/findings` with tenant isolation and RBAC (QA_AND_ABOVE)
- Optional filters: severity, status, module_id, programme_id, date range

**Frontend:**
- Create `frontend/src/app/(main)/findings/FindingsView.tsx`
- List with severity badges (critical/high/medium/low), status, module name, finding type
- Filter panel (severity, status, date)
- Row click → audit run detail

---

### P1.2 — Implement Accreditation Readiness Page (KI-004)

**Why P1:** The accreditation readiness agent is complete and triggers successfully. There is no way to view its output through the UI.

**Frontend:**
- Create `frontend/src/app/(main)/accreditation/AccreditationView.tsx`
- Show: list of accreditation audit runs per institution/programme; readiness score; key findings; trigger button for coordinators+

---

### P1.3 — Fix Knowledge Search (KI-005)

**Why P1:** Semantic knowledge search is listed as a feature on the Knowledge landing page. `GET /api/v1/knowledge-search` → 405.

**Investigation:**
- Read `backend/app/routes/knowledge_index.py` or whichever file handles search
- Determine correct HTTP method (POST with body?) and correct path
- Fix route mounting or update frontend hook to use correct method/path

---

## P2: Medium-Priority Completions

### P2.1 — Implement Settings Pages (KI-006)

**Priority order within settings:**
1. **Profile** — display name and current institution (read-only acceptable initially)
2. **Security** — password change form
3. **Notifications** — toggle email/in-app notification preferences
4. **System** (SA only) — system configuration

---

### P2.2 — Implement Compliance Report Page (KI-007)

**What to do:**
- Create `frontend/src/app/(main)/reports/compliance/ComplianceReportView.tsx`
- Call `GET /api/v1/reporting/compliance-summary`
- Render: compliance score by faculty/department, trend if available, export button

---

### P2.3 — Fix PDF Export (KI-008)

**What to do:**
- Add `reportlab` or `weasyprint` to `backend/requirements.txt`
- Update `GET /api/v1/reporting/export/pdf` to generate a real PDF
- Update content-type to `application/pdf`

---

### P2.4 — Verify and Fix Qualification Search (KI-009)

**What to do:**
- Read `backend/app/routes/qualification.py` to find the correct search endpoint
- Fix path in frontend or fix route mounting
- Test: `GET /api/v1/qualification/{correct-path}` with a qualification name query

---

### P2.5 — Live Test Dean / HOD / Coordinator Roles (KI-013)

**What to do:**
- Log in as a seeded dean user (e.g., `dean.engineering@tut.ac.za`)
- Verify: 4-workspace sidebar, can trigger audits, Reports visible for Dean / hidden for HOD
- Log in as a seeded coordinator
- Verify: 4-workspace sidebar, can trigger audits, Audit Centre shows runs for their programme

---

## P3: Cleanup and Polish

### P3.1 — Remove Old `/ai-assistant` Route (KI-010)

**What to do:**
1. Delete `frontend/src/app/(main)/ai-assistant/` directory
2. Add redirect in `next.config.js`:
```js
async redirects() {
  return [{ source: '/ai-assistant', destination: '/ai-workspace', permanent: true }]
}
```

---

### P3.2 — Confirm Redis Usage (KI-011)

**What to do:**
- `grep -r "redis" backend/app/ --include="*.py"`
- Document what Redis is used for in CLAUDE.md Infrastructure Notes

---

### P3.3 — Resolve MongoDB Architecture Decision (KI-012)

**What to do:**
- Decide: is MongoDB needed for any planned feature?
- If no: remove MongoDB reference from CLAUDE.md
- If yes: add container to docker-compose; create connection module; document intended use

---

## Recommended Execution Order

```
Phase 5 — Functional Completion

Sprint 1 (P0):
  ├── P0.1: Real semantic embeddings
  └── P0.2: Fix global audit list

Sprint 2 (P1):
  ├── P1.1: Findings page (frontend + backend route)
  ├── P1.2: Accreditation readiness page
  └── P1.3: Knowledge search fix

Sprint 3 (P2):
  ├── P2.1: Settings — Profile + Security
  ├── P2.2: Compliance report page
  ├── P2.3: PDF export
  └── P2.5: Live test Dean/HOD/Coordinator

Sprint 4 (P2-P3):
  ├── P2.4: Qualification search
  ├── P3.1: Remove /ai-assistant
  └── P3.2/3: Redis/MongoDB cleanup
```

---

## What NOT to Do Next

- Do not start new UI redesigns before fixing KI-001 and KI-002. The design is already at commercial standard.
- Do not add new AI features before semantic embeddings are working.
- Do not add new placeholder pages. Remove existing ones instead.
- Do not redesign any page that currently has a working View implementation.
- Do not build new admin features before the existing 8 placeholder pages have been implemented.

---

## Success Criteria for Phase 5

Phase 5 will be complete when:
1. `GET /api/v1/ai-assistant/ask` returns `"is_placeholder_mode": false`
2. `GET /api/v1/audits` returns completed audit runs (not empty)
3. `/findings` renders a real findings list (not PlaceholderPage)
4. `/accreditation` renders a real accreditation view (not PlaceholderPage)
5. `/settings/profile` and `/settings/security` render real forms (not PlaceholderPage)
6. All 7 user roles have been live-tested in browser (currently: 4 confirmed)
7. `python -m pytest -q` still passes 1,198+ tests
8. `npx tsc --noEmit` still shows 0 errors
