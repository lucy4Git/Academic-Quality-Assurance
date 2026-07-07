# Integration Sprint — Live Data Wiring

**Document ID:** IMPL-INT-001
**Status:** Complete
**Last Updated:** 2026-07-07
**Depends on:** Split 2 Wave 1 (Institutional Knowledge Foundation)

---

## Purpose

Wave 1 delivered the institutional knowledge data model (11 models), a seed
data package (26 SA universities, provenance-tagged), and read-only overview
endpoints. This sprint connects that foundation to the live product surface:
the dashboard, the Knowledge Foundation page, and the Institution Profile page
now render **real database counts** instead of hardcoded demo values.

---

## New Backend Endpoints

All live under the existing router `backend/app/routes/institution_knowledge.py`
(prefix `/api/v1/institution-knowledge`). All are `AnyAuthenticatedUser` and
enforce tenant isolation via `_resolve_scope()`:

- **System Admin** — may pass `?institution_id=<uuid>` to scope to one
  institution, or omit it for platform-wide aggregate counts.
- **All other roles** — the `institution_id` query param is ignored; they are
  locked to their own `institution_id`.

| Endpoint | Response schema | Notes |
|----------|-----------------|-------|
| `GET /live-counts` | `LiveCountsResponse` | Per-entity counts for all 15 Wave 1 entity tables. |
| `GET /provenance-summary` | `ProvenanceSummaryResponse` | `{entity: {data_status: count}}` map. |
| `GET /coverage-summary` | `CoverageSummaryResponse` | Provenance percentages + RAG/crawler readiness + missing-data warnings. |
| `GET /institutions/{id}/full-profile` | `FullInstitutionProfile` | One-shot profile payload. Students get only public data. |

### Readiness heuristics (`/coverage-summary`)

- **RAG readiness** — ratio of trustworthy records (`public_verified + needs_review`)
  over all provenance-bearing records:
  `> 0.7 → ready`, `> 0.3 → partial`, else `not_ready`.
- **Crawler readiness** — structural completeness: all of campuses, faculties,
  departments have entries → `ready`; some present → `partial`; none → `not_ready`.

### Counting pattern

Counts use the async SQLAlchemy pattern already established in the file:

```python
result = await db.execute(select(func.count()).select_from(Model).where(...))
result.scalar()
```

Institution scoping walks the hierarchy with subquery `IN` filters
(`Faculty → Department → Programme → Module → LearningOutcome`), and
`PolicyVersion` is scoped through its parent `Policy`. `AccreditationBody` is
global reference data and is never institution-scoped.

---

## Schemas

Added to `backend/app/schemas/institution_knowledge.py`:
`LiveCountsResponse`, `ProvenanceSummaryResponse`, `CoverageSummaryResponse`,
`FacultyWithDeptCount`, `FullInstitutionProfile`.

---

## Frontend Wiring

- **API client** (`frontend/src/lib/api/institutionKnowledge.ts`) — new types
  `LiveCountsResponse`, `CoverageSummaryResponse`, `FullInstitutionProfile` and
  functions `getLiveCounts`, `getCoverageSummary`, `getFullInstitutionProfile`.
  All calls go through the shared `apiClient` (which routes via the Next.js
  `/api/proxy/...` handler — the browser never calls FastAPI directly).
- **Hooks** (`frontend/src/hooks/useInstitutionKnowledge.ts`) — new TanStack
  Query hooks `useInstitutionKnowledgeLiveCounts`, `useCoverageSummary`,
  `useFullInstitutionProfile`.
- **Dashboard** (`app/(main)/dashboard/page.tsx`) — three KPI cards now show
  live Modules / Policies / Documents counts; a loading placeholder (`—`) plus
  "Demo data" label shows while loading, replaced by the count and a green
  "Live" indicator once resolved.
- **Knowledge Foundation** (`app/(main)/knowledge/foundation/page.tsx`) —
  entity count grid is driven by `/live-counts`; RAG + crawler readiness badges
  and missing-data warnings come from `/coverage-summary`.
- **Institution Profile** (`app/(main)/institution/profile/page.tsx`) —
  rebuilt on `/full-profile`, with a System Admin institution selector and
  per-record provenance badges across campuses, faculties, policies, documents,
  contacts, and accreditations.

---

## AI Assistant Error Safety

`POST /api/v1/ai-assistant/ask` (non-streaming) previously called
`advanced_ask(...)` with no guard, so an internal failure surfaced as a raw
500. It is now wrapped: the exception is logged with `logger.exception(...)`
and re-raised as HTTP 503 with the safe detail
`"AI service temporarily unavailable. Please try again."` — no stack trace or
provider internals reach the client. The streaming endpoint already emitted a
safe `error` SSE event, and the frontend `AiErrorCard` (in `AiWorkspaceView.tsx`)
was verified to render correctly on `msg.isError`.

---

## Route Permissions

`/knowledge/foundation` and `/institution/profile` were already registered as
`STAFF` in `frontend/src/lib/rbac.ts`; the 7-item flat `NAV_SECTIONS` from
Split 1 is unchanged.
