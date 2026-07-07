# Integration Sprint — Testing Guide

**Document ID:** TEST-INT-001
**Status:** Complete
**Last Updated:** 2026-07-07

---

## 1. Automated tests

```bash
cd backend
python -m pytest tests/test_integration_sprint.py -q     # 13 tests
python -m pytest -q                                       # full suite (1125 tests)
```

`test_integration_sprint.py` covers:
- verification script presence and expected-count constants,
- all 11 Wave 1 models importable with correct table names,
- registration of the four new endpoints (`live-counts`, `provenance-summary`,
  `coverage-summary`, `full-profile`),
- AI assistant router present and `AiErrorCard` wired in the workspace view,
- frontend type/hook presence,
- data-package completeness (15 JSON files, 2000+ modules).

> **Environment note:** the suite requires `backend/.env` to be present
> (provides `SECRET_KEY` and `DATABASE_URL`). Importing any `app.routes.*`
> module instantiates `Settings`, which fails collection if `.env` is missing.
> In a fresh git worktree `.env` is not carried over (it is gitignored); copy it
> from the primary checkout before running tests.

---

## 2. Verification script

Read-only; safe against a live database. Checks actual row counts against the
Wave 1 targets and prints a provenance breakdown plus samples.

```bash
cd backend
python ../database/seed_data/verify_institution_knowledge_foundation.py
```

Expected: every entity at or above its target (institutions 26, campuses 46,
modules 2082, learning_outcomes 4164, policies 130, …). Rows below target print
`⚠️`/`❌` and the trailer advises re-running the seed pipeline.

---

## 3. Manual endpoint checks

With the backend running (`uvicorn app.main:app --reload --port 8000`) and a
valid Bearer token:

```bash
# Live counts (own institution for non-admin; add ?institution_id= as System Admin)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/institution-knowledge/live-counts

# Coverage summary — readiness scores + warnings
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/institution-knowledge/coverage-summary

# Full profile for one institution
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/institution-knowledge/institutions/$INST_ID/full-profile
```

Tenant-isolation checks:
- A non-admin requesting another institution's `full-profile` → **403**.
- A non-admin passing `?institution_id=<other>` to `live-counts` → counts are
  silently scoped to **their own** institution (param ignored), never the other.
- A student on `full-profile` → only basic profile, public campuses, public
  contacts; no policies/documents/accreditations/coverage.

---

## 4. Frontend validation

```bash
cd frontend
npm install            # required in a fresh worktree (no node_modules)
npx tsc --noEmit --skipLibCheck    # expect 0 errors
npm run dev            # http://localhost:3000
```

- **Dashboard** — Modules / Policies / Documents cards show `—` then live
  numbers with a green "Live" indicator.
- **/knowledge/foundation** — count grid populated from `/live-counts`; RAG and
  crawler readiness badges and any missing-data warnings render.
- **/institution/profile** — full profile with provenance badges; System Admin
  sees the institution selector.

---

## 5. AI assistant error path

Force a provider failure (e.g. invalid `AI_PROVIDER` config) and POST to
`/api/v1/ai-assistant/ask`. Expected: HTTP **503** with detail
`"AI service temporarily unavailable. Please try again."` and a logged
`AI ask failed` server-side — no stack trace in the response body. In the
AI workspace UI, the `AiErrorCard` renders with a retry affordance.
