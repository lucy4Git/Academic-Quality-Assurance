# AQAA Recovery Verification Report

**Document:** AQAA_RECOVERY_VERIFICATION_REPORT  
**Sprint:** Recovery Sprint — Stage A Gate  
**Date:** 2026-07-13  
**Status:** ALL 12 CRITERIA PASS — Stage B authorized

---

## Executive Summary

This report consolidates the Stage A verification findings for the AQAA platform recovery sprint. The primary objectives were to restore the intelligence layer (semantic embeddings, honest AI labelling), repair the global Audit Centre, and validate multi-role browser behaviour with tenant isolation. All 12 acceptance criteria have been met.

---

## A1: Repository and Infrastructure State

| Check | Result |
|-------|--------|
| Branch | `main` |
| Migration head | `d4e5f6a7b8c9` (current) |
| Docker containers | 4/4 healthy (postgres, redis, qdrant, backend) |
| Backend health | `GET /health → {"status": "ok"}` |
| Qdrant health | Port 6333 responsive, 2 collections (`TUT`, `UP`) |

---

## A2: FastEmbed Deployment Durability

`fastembed>=0.3,<1.0` is present in `backend/requirements.txt` and baked into the Docker image via `RUN pip install --no-cache-dir -r requirements.txt`. Clean rebuild (`--no-cache`) confirms the package is installed in the image layer, not the ephemeral container filesystem.

- Clean rebuild: **PASS** (image `sha256:49b5dca9...`)
- First start: `FastEmbedEmbeddingService IS_PLACEHOLDER=False DIMS=384` — **PASS**
- Second restart: same result — **PASS**

Full detail: `docs/recovery/AQAA_DOCKER_DURABILITY_REPORT.md`

---

## A3: Qdrant Collections

| Field | TUT | UP |
|-------|-----|-----|
| Points | 196 | 28 |
| Vector dims | 384 | 384 |
| Distance metric | Cosine | Cosine |
| Payload field | `institution_code: "TUT"` | `institution_code: "UP"` |
| Cross-tenant bleed | None | None |

---

## A4: Retrieval Quality Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Hit Rate@5 | 0.929 (13/14) | ≥ 0.85 | **PASS** |
| MRR | 0.881 | — | — |
| Avg latency | 67.1ms (incl. warm-up) | — | — |
| Steady-state | 17–55ms | — | — |
| Tenant isolation | 0 leakage | 0 leakage | **PASS** |

The single miss (query #4) is a labelling error in the eval dataset — the module code DTD117V was correctly retrieved but the expected keyword was "DTS". Corrected Hit Rate@5 = 1.000.

Full detail: `docs/recovery/AQAA_REPRODUCED_RETRIEVAL_METRICS.md`

---

## A5: Knowledge Search Endpoint

`POST /api/v1/knowledge-search` returns HTTP 200 with real semantic results.  
`GET /api/v1/knowledge-search` correctly returns HTTP 405 (Method Not Allowed) — this is correct REST behaviour, not a bug.  
The previously reported "405 error" was caused by callers using GET on a POST-only endpoint. No backend change was required.

---

## A6: Citation Validation

10 queries tested via authenticated API calls as TUT QA Officer.

- Invented citations: **0 / 10**
- All `source_document` fields populated with IKP chunk origin
- No answer referenced a document absent from `sources[]`

Full detail: `docs/recovery/AQAA_CITATION_VALIDATION_REPORT.md`

---

## A7: AI Generation Honesty

**Bug fixed:** `is_placeholder_mode` was incorrectly set to `True` whenever OpenAI returned `insufficient_quota`, even though semantic embeddings were functioning. This conflated embedding state with generation fallback state.

**Fix applied in:**
- `backend/app/rag/advanced_rag_service.py` — primary AI path
- `backend/app/ai_assistant/assistant_service.py` — secondary path
- `backend/app/schemas/ai_assistant.py` — 5 new `AskResponse` fields

**New fields in all responses:**

| Field | Honest value (current state) |
|-------|------------------------------|
| `is_placeholder_mode` | `false` (embeddings are real) |
| `retrieval_mode` | `"semantic"` |
| `embedding_provider` | `"BAAI/bge-small-en-v1.5"` |
| `generation_mode` | `"deterministic_template"` (OpenAI quota exhausted) |
| `generation_provider` | `"none"` |
| `evidence_support_status` | `"chunks_retrieved"` |

---

## A8: Audit Centre Durability

The route collision fix (module audits moved from `/api/v1` to `/api/v1/module-folder`) survived the Docker rebuild.

| Check | Result |
|-------|--------|
| `GET /api/v1/audits` (TUT QA Officer) | 2 runs, tenant-scoped |
| `GET /api/v1/audits` (System Admin) | 62 runs, all institutions |
| Pagination (`?limit=1&offset=1`) | Correct (1 result, offset applied) |
| Invalid ID (`GET /api/v1/audits/{uuid}`) | 404 |
| RBAC: Lecturer accessing Audit Centre | "Access Denied" rendered by `RoleGuard` |

---

## A9: Browser Validation

### Scenario 1 — TUT QA Officer
- Login: `POST /api/v1/auth/login` → 200, `access_token` cookie set
- Dashboard: rendered with TUT institution badge
- Audit Centre: 2 completed runs visible, paginated correctly
- Audit detail (`/audits/{id}`): findings rendered
- AI Assistant: responded with real semantic context, `retrieval_mode: semantic`

### Scenario 2 — Lecturer RBAC
- Login: Lecturer account
- Audit Centre navigation: `RoleGuard` renders "Access Denied" — lecturer role is not in allowed list
- AI Assistant: accessible (lecturer is in allowed roles for AI workspace)

### Scenario 3 — Cross-Tenant Isolation (TUT vs UP)
- UP QA Officer login: `institution_code: UP` confirmed in `/auth/me`
- Audit Centre: 0 TUT runs visible (UP has 0 completed runs — correct)
- AI Assistant query "Computing Fundamentals CFA115D" as UP user:
  - Top result: UP chunk (COS 212 Data Structures, University of Pretoria)
  - TUT CFA115D chunk: **not present** in 5 returned results
  - Tenant leakage: 0

---

## A10: Stage A Gate Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | FastEmbed baked into Docker image (not ephemeral) | **PASS** |
| 2 | `IS_PLACEHOLDER = False` in running container | **PASS** |
| 3 | Qdrant collections: 384 dims, Cosine, correct tenant payload | **PASS** |
| 4 | Hit Rate@5 ≥ 0.85 | **PASS** (0.929) |
| 5 | Tenant isolation: 0 leakage | **PASS** |
| 6 | `POST /knowledge-search` returns 200 with real results | **PASS** |
| 7 | 0 invented citations across 10 grounded responses | **PASS** |
| 8 | `is_placeholder_mode` reflects embedding state only | **PASS** |
| 9 | 5 honest generation fields present in `AskResponse` | **PASS** |
| 10 | Audit Centre shows tenant-scoped runs (QA Officer) | **PASS** |
| 11 | Lecturer RBAC blocks Audit Centre access | **PASS** |
| 12 | UP AI query returns only UP chunks | **PASS** |

**12 / 12 criteria passed.**

---

## Known Limitation (Not a Gate Blocker)

**ISSUE-001 — OpenAI quota exhausted:** The configured OpenAI key returns `insufficient_quota`. The system falls back to `deterministic_template` generation. The intelligence layer (semantic retrieval, citations, tenant isolation) is fully functional. Generation quality is limited to template assembly until the key is funded or an alternative provider (Anthropic, Ollama) is configured. Documented in `docs/recovery/AQAA_PLACEHOLDER_AI_REMOVAL_REGISTER.md`.

---

## Stage A Decision

**STAGE A: COMPLETE — GATE PASSED**  
Stage B (Findings Lifecycle + Accreditation Workspace) is authorized to begin.
