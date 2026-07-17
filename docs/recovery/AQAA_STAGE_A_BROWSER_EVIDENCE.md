# AQAA Stage A Browser Evidence

**Document:** AQAA_STAGE_A_BROWSER_EVIDENCE  
**Sprint:** Recovery Sprint — Stage A9  
**Date:** 2026-07-13  
**Status:** ALL SCENARIOS PASS

---

## Test Environment

| Field | Value |
|-------|-------|
| Frontend | Next.js 14 dev server, `http://localhost:3000` |
| Backend | FastAPI 0.115, `http://localhost:8000` |
| Browser | Chromium via Claude in-app browser panel |
| Auth method | httpOnly cookie (`access_token`), proxy at `/api/proxy/` |
| Test date | 2026-07-13 |

---

## Scenario 1: TUT QA Officer — Full Workflow

### Step 1.1 — Login

**Action:** `POST /api/v1/auth/login` with TUT QA Officer credentials  
**Result:** HTTP 200, `access_token` cookie set  
**UI:** Redirected to `/dashboard`; TUT badge and institution name rendered in navigation header

### Step 1.2 — Dashboard

**Action:** Navigate to `/dashboard`  
**Result:** Dashboard rendered with TUT branding, compliance summary widgets loaded  
**Evidence:** Institution badge reads "TUT" in navigation sidebar

### Step 1.3 — Audit Centre

**Action:** Navigate to `/audits`  
**Result:** Audit Centre loaded; 2 completed AI audit runs visible  
**Data:** Runs are TUT-only — no UP or other institution runs present  
**Evidence:** Table shows `institution_code: TUT` in run metadata

### Step 1.4 — Audit Detail

**Action:** Click first audit run → `/audits/{id}`  
**Result:** Audit detail page loaded; findings rendered with severity badges  
**Data:** Findings array populated (agent_type, module_id, findings[])

### Step 1.5 — AI Assistant

**Action:** Navigate to `/ai-workspace`, submit question: "What modules are in the DPRS20 programme?"  
**Result:** Response received with semantic sources  
**Response fields verified:**
- `retrieval_mode: "semantic"`
- `is_placeholder_mode: false`
- `embedding_provider: "BAAI/bge-small-en-v1.5"`
- `generation_mode: "deterministic_template"`
- `evidence_support_status: "chunks_retrieved"`
- `sources[].source_document` populated (IKP chunk references)

---

## Scenario 2: Lecturer RBAC Enforcement

### Step 2.1 — Login

**Action:** Login with Lecturer account credentials  
**Result:** HTTP 200, session established  
**UI:** Dashboard rendered with Lecturer role indicator

### Step 2.2 — Audit Centre RBAC Block

**Action:** Navigate to `/audits`  
**Result:** `RoleGuard` component evaluated `user.role === "lecturer"` — role not in allowed list  
**UI:** "Access Denied" message rendered; Audit Centre content not shown  
**Evidence:** No API call made to `GET /api/v1/audits` — client-side guard prevents even the fetch

### Step 2.3 — AI Workspace Access

**Action:** Navigate to `/ai-workspace`  
**Result:** AI Workspace accessible — `lecturer` role is in the allowed list for AI access  
**UI:** Chat interface rendered; question input active

---

## Scenario 3: Cross-Tenant Isolation — UP QA Officer

### Step 3.1 — Login

**Action:** Login with UP QA Officer credentials  
**Result:** HTTP 200, `access_token` cookie set  
**API verification:** `GET /api/v1/auth/me` → `{ "institution_code": "UP", "role": "quality_assurance_officer" }`

### Step 3.2 — Audit Centre Isolation

**Action:** Navigate to `/audits`  
**Result:** "0 completed · 0 total" — no TUT audit runs visible  
**Analysis:** UP has no completed AI audit runs (no agents have been triggered for UP modules). This is the correct result — not a rendering error.  
**Tenant isolation:** TUT runs (62 total in system) not visible to UP user — **PASS**

### Step 3.3 — AI Assistant Tenant Isolation

**Action:** Submit question "Computing Fundamentals CFA115D" as UP user via AI Workspace  
**Expected:** Only UP knowledge chunks returned; TUT CFA115D chunk absent  
**Result:**
- Top result: UP chunk — "COS 212 Data Structures and Algorithms, University of Pretoria" 
- Chunks 2–5: UP module/programme metadata
- TUT CFA115D: **NOT PRESENT** in any of 5 returned chunks
- `institution_code: "UP"` in response

**Tenant leakage: 0** — **PASS**

### Step 3.4 — API-Level Isolation Verification

**Direct API test:** `POST /api/v1/knowledge-search` with `{"query": "CFA115D", "institution_code": "UP", "top_k": 5}`  
**Result:** 5 chunks, all from UP Qdrant collection  
**TUT CFA115D chunk:** absent  
**Qdrant filter confirmed:** `must: [{ "key": "institution_code", "match": { "value": "UP" } }]`

---

## Summary of Browser Evidence

| Scenario | Check | Result |
|----------|-------|--------|
| TUT QA Officer | Login + session | PASS |
| TUT QA Officer | Dashboard with TUT branding | PASS |
| TUT QA Officer | Audit Centre — 2 TUT runs only | PASS |
| TUT QA Officer | Audit detail with findings | PASS |
| TUT QA Officer | AI Assistant — semantic retrieval | PASS |
| TUT QA Officer | `is_placeholder_mode: false` | PASS |
| Lecturer | Login | PASS |
| Lecturer | Audit Centre — "Access Denied" | PASS |
| Lecturer | AI Workspace — accessible | PASS |
| UP QA Officer | Login — `institution_code: UP` | PASS |
| UP QA Officer | Audit Centre — 0 TUT runs visible | PASS |
| UP QA Officer | AI query — 0 TUT chunks returned | PASS |

**12 / 12 browser checks passed.**
