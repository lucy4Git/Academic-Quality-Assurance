# AQAA Phase D — Release Notes

**Release:** v0.9.0-phase-d
**Date:** 2026-07-17
**Branch:** `recovery/semantic-grounding-and-audit-centre`
**Base commit:** `5b6e211`

---

## Overview

Phase D delivers the AI-native universal workspace: a conversational operating system for Higher Education Quality Assurance. This release transforms AQAA from a structured audit platform into an always-on AI workspace where QA operations happen inside natural language sessions.

---

## New Features

### AI-Native Universal Workspace

A three-panel conversational interface with:
- Left sidebar: session history with pin, rename, archive
- Main panel: streaming AI responses with structured domain cards
- Right panel: live knowledge context — active module, Qdrant sources, semantic grounding status

### Conversation Persistence

- Full session/message persistence to PostgreSQL
- Session restore on reload — conversations survive browser refresh
- `GET /api/v1/ai-assistant/sessions` — paginated session list
- `GET /api/v1/ai-assistant/sessions/{id}` — full session with messages + artifacts

### Module Context Establishment via SSE

- `POST /api/v1/ai-assistant/ask-stream` — Server-Sent Events streaming
- SSE `context` event sets `activeModuleId` in React state from a live query response
- Module context gates file attachment — attach button disabled until context established
- Context panel shows `LIVE CONTEXT` with module code and name

### Semantic Attachment Grounding

- 6-stage attachment pipeline: `REQUESTED → FOUND → LOADED → PARSED → USED / FAILED`
- `attachment_grounding_status`: `not_requested / requested / success / partial / failed`
- ZIP parser expanded: supports `.zip` containing `.pdf`, `.docx`, `.txt`, `.xlsx`, `.csv`
- Attachment content injected into RAG context before answer generation
- Citation links in responses reference attached files by name

### Findings Lifecycle Integration

- AI Workspace triggers finding intents: draft → submit → approve/reject/reopen/close
- Finding state machine enforced in backend — invalid transitions rejected
- Finding history tracked with timestamps and actor

### Artifacts and Actions

- AI-generated artifacts (Markdown, JSON) saved to `ai_artifacts` table
- `POST /api/v1/ai-assistant/sessions/{id}/artifacts` — create artifact
- `GET /api/v1/ai-assistant/sessions/{id}/artifacts` — list artifacts
- Export: JSON and Markdown formats only (PDF/DOCX/XLSX not implemented in this release)

### Regulatory Framework Engine Integration

- `source_status` field on all regulatory document tables: `VERIFIED / PENDING_VERIFICATION / SUPERSEDED / NOT_FOUND`
- Anti-hallucination guard: AI responses cite `source_status` on regulatory references
- No regulatory standard is hard-coded — all citations draw from seeded knowledge base

### Multi-Tenant Security Controls

- Sessions: ownership enforced — cross-session access returns `403 Forbidden`
- Module/programme endpoints: cross-tenant access returns `404 Not Found` (avoids leaking resource existence)
- Qdrant queries filtered by `institution_id` — no cross-institution vector bleed

---

## Bug Fixes

- **ZIP MIME type**: Frontend now accepts `application/zip`, `application/x-zip-compressed`, `application/octet-stream`, `multipart/x-zip`, and `application/x-compressed` in addition to `application/zip` only
- **Session restoration**: `activeModuleId` correctly requires a live SSE `context` event — not restored from session history (prevents stale context)
- **Structured blocks and citations**: Fixed persistence in `ask-stream` route — `structured_blocks` and `citations` now saved to `ai_chat_messages` on stream completion
- **Artifacts in session response**: `GET /sessions/{id}` now includes `artifacts[]` array

---

## Known Limitations

See [AQAA_PHASE_D_KNOWN_LIMITATIONS.md](AQAA_PHASE_D_KNOWN_LIMITATIONS.md) for the complete register.

Notable limitations in this release:
- File picker cannot be invoked inside the in-app Claude Browser (system dialog limitation); upload verified via HTTP API
- Export formats: JSON and Markdown only — PDF, DOCX, XLSX not implemented
- Qdrant backup: snapshot API available but reindex-from-source recommended at current data volume
- MongoDB: architected but not wired
- No real-time multi-user collaboration (single-user session model)

---

## Test Coverage

| Suite | Tests | Result |
|-------|-------|--------|
| Backend (pytest) | 1,319 | All pass |
| Frontend (TypeScript) | 0 errors | Clean build |
| Production build | Next.js 14.2.35 | Compiled successfully |
| Regression smoke tests | 12 endpoints | All pass |

---

## Migration

This release adds migration `7602e7b39d25` (Phase D artifacts, actions, session extensions) on top of migration `51694630069f`.

**To upgrade from Phase C:**
```bash
cd backend && python -m alembic upgrade head
```

**Rollback to Phase C:**
```bash
cd backend && python -m alembic downgrade 51694630069f
```

---

## Infrastructure

No infrastructure changes from Phase C. Same 4-service Docker Compose stack. See [AQAA_PHASE_D_DOCKER_SERVICE_MANIFEST.md](AQAA_PHASE_D_DOCKER_SERVICE_MANIFEST.md).

---

## Contributors

AQAA Engineering
