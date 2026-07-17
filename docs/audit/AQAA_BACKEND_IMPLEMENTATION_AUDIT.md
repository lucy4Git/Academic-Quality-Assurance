# AQAA Backend Implementation Audit

**Audit Date:** 2026-07-13  
**Stack:** FastAPI, Python 3.13, SQLAlchemy 2 (async), asyncpg, Alembic  
**Test count:** 1,198 passing (verified live)  
**Methodology:** File enumeration + direct route/service inspection + live API testing

---

## 1. Architecture

### Entry Point
`backend/app/main.py` — `create_app()`:
- FastAPI instance with CORS middleware
- Domain exception → HTTP status mapping
- `/health` endpoint
- All routers mounted under `/api/v1`

### Configuration
`backend/app/config.py` — Pydantic `Settings` from `backend/.env`:
- `SECRET_KEY` — JWT signing
- `DATABASE_URL` — PostgreSQL connection
- `CORS_ORIGINS` — comma-separated, parsed via `NoDecode`
- `STORAGE_BACKEND`, `MAX_UPLOAD_SIZE_MB`

### Data Model Hierarchy
```
Institution → Faculty → Department → Programme → Module
```
All models inherit: `Base`, `UUIDPrimaryKeyMixin`, `TimestampMixin` from `backend/app/models/base.py`

**Known fix (do not revert):** `Faculty.__tablename__ = "faculties"` — overrides naive pluralisation to `"facultys"`.

---

## 2. Routes (37 route files)

| Route File | Prefix | Status |
|-----------|--------|--------|
| `auth.py` | `/api/v1/auth` | COMPLETE_AND_VERIFIED |
| `institutions.py` | `/api/v1/institutions` | COMPLETE_AND_VERIFIED |
| `faculties.py` | `/api/v1/faculties` | COMPLETE_AND_VERIFIED |
| `departments.py` | `/api/v1/departments` | COMPLETE_AND_VERIFIED |
| `programmes.py` | `/api/v1/programmes` | COMPLETE_AND_VERIFIED |
| `modules.py` | `/api/v1/modules` | COMPLETE_AND_VERIFIED |
| `files.py` | `/api/v1/files` | COMPLETE_BUT_NOT_VERIFIED |
| `audits.py` | `/api/v1/audits` | PARTIALLY_IMPLEMENTED (global list broken) |
| `module_audits.py` | `/api/v1/module-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `assessment_audits.py` | `/api/v1/assessment-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `moderation_audits.py` | `/api/v1/moderation-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `attendance_audits.py` | `/api/v1/attendance-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `evidence_audits.py` | `/api/v1/evidence-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `outcome_alignment_audits.py` | `/api/v1/outcome-alignment-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `accreditation_readiness_audits.py` | `/api/v1/accreditation-readiness-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `programme_review_audits.py` | `/api/v1/programme-review-audits` | COMPLETE_BUT_NOT_VERIFIED |
| `audit_evidence.py` | `/api/v1/audit-evidence` | COMPLETE_BUT_NOT_VERIFIED |
| `ai_assistant.py` | `/api/v1/ai-assistant` | PARTIALLY_IMPLEMENTED (placeholder embeddings) |
| `workflow.py` | `/api/v1/workflow` | COMPLETE_BUT_NOT_VERIFIED |
| `approvals.py` | `/api/v1/approvals` | COMPLETE_BUT_NOT_VERIFIED |
| `comments.py` | `/api/v1/comments` | COMPLETE_BUT_NOT_VERIFIED |
| `notifications.py` | `/api/v1/notifications` | COMPLETE_BUT_NOT_VERIFIED |
| `reporting.py` | `/api/v1/reporting` | COMPLETE_BUT_NOT_VERIFIED |
| `reports.py` | `/api/v1/reports` | UNKNOWN (distinct from reporting?) |
| `providers.py` | `/api/v1/providers` | COMPLETE_AND_VERIFIED (health endpoint) |
| `admin.py` | `/api/v1/admin` | COMPLETE_BUT_NOT_VERIFIED |
| `acquisition.py` | `/api/v1/acquisition` | COMPLETE_AND_VERIFIED |
| `extraction.py` | `/api/v1/extraction` | COMPLETE_AND_VERIFIED |
| `ikp.py` | `/api/v1/ikp` | COMPLETE_BUT_NOT_VERIFIED |
| `institution_knowledge.py` | `/api/v1/institution-knowledge` | COMPLETE_BUT_NOT_VERIFIED |
| `knowledge_index.py` | `/api/v1/knowledge-index` | COMPLETE_BUT_NOT_VERIFIED |
| `knowledge_review.py` | `/api/v1/knowledge-review` | COMPLETE_BUT_NOT_VERIFIED |
| `qualification.py` | `/api/v1/qualification` | PARTIALLY_IMPLEMENTED (search → 404) |
| `processing.py` | `/api/v1/processing` | UNKNOWN |
| `workspace.py` | `/api/v1/workspace` | UNKNOWN |
| `dashboard.py` | `/api/v1/dashboard` | COMPLETE_AND_VERIFIED |
| `audit_history_service.py` | (service only) | N/A |

---

## 3. Models (38 model files)

The PostgreSQL schema covers:
- `User`, `Institution`, `Faculty`, `Department`, `Programme`, `Module` — core hierarchy
- `AuditRun`, `Finding`, `AuditEvidence`, `AuditHistory` — audit domain
- `WorkflowItem`, `Comment`, `Notification` — workflow domain
- `AIChat`, `AIChatMessage` — AI conversation persistence
- `Qualification`, `QualificationSearch` — qualification intelligence
- `KnowledgeReview`, `KnowledgeIndexEntry` — knowledge pipeline
- `AcquisitionSource`, `CrawlJob` — acquisition engine
- `ExtractionJob`, `ExtractedContent` — extraction engine
- `IKPRegistry`, `InstitutionKnowledge` — IKP foundation
- `FileUpload` — file management
- `UserRegistration` — extended user fields

**Key enum types (all `str` enums):**
`UserRole`, `ProgrammeLevel`, `FileCategory`, `AgentType`, `AuditRunStatus`, `AuditStatus`, `FindingSeverity`, `FindingType`, `UploadState`, `WorkflowStatus`

---

## 4. Services (41 service files)

Complete service layer exists for all major domains. Key services:
- `auth_service.py` — login, token generation
- `institution_service.py` — CRUD + tenant scoping
- `audit_service.py` — orchestration
- `module_audit_service.py` through `accreditation_readiness_service.py` — 7 agent services
- `workflow_service.py` — assignment and status transitions
- `report_service.py` — aggregate reporting
- `extraction_service.py` — content extraction
- `qualification_service.py` — qualification intelligence
- `dashboard_service.py` — home page stats
- `agent_router_service.py` — routes requests to correct agent

---

## 5. AI Agents (8 agents, 16 files — dual file per agent)

Each agent has two files: a domain orchestrator (`*_compliance.py`, `*_readiness.py`) and an agent class (`*_agent.py`):

| Agent | Trigger Path | Scope |
|-------|-------------|-------|
| Module Folder Audit | `/audits/modules/{id}/trigger` | Module |
| Assessment Compliance | `/assessment-audits/modules/{id}/trigger` | Module |
| Moderation Compliance | `/moderation-audits/modules/{id}/trigger` | Module |
| Attendance Compliance | `/attendance-audits/modules/{id}/trigger` | Module |
| Evidence Verification | `/evidence-audits/modules/{id}/trigger` | Module |
| Outcome Alignment | `/outcome-alignment-audits/modules/{id}/trigger` | Module |
| Accreditation Readiness | `/accreditation-readiness-audits/modules/{id}/trigger` | Module |
| Programme Review | `/programme-review-audits/programmes/{id}/trigger` | Programme |

All triggers: `POST` → HTTP 202 immediately, background task, `run_id` returned.  
Polling: `GET /api/v1/audits/{run_id}` until `run_status` ∈ `{completed, failed}`.

Common file: `scoring_common.py` — shared scoring logic.

---

## 6. Authentication System

- Login: `POST /api/v1/auth/login` (JSON) or `POST /api/v1/auth/token` (OAuth2 form)
- Tokens: HS256 JWTs, `SECRET_KEY` from config
- Access token: 60 min; refresh token: 7 days
- `backend/app/dependencies.py`: `get_current_user`, `AdminRequired`, `QAOfficerRequired`, `CoordinatorRequired`, `AnyAuthenticatedUser`
- **Critical**: Named role shortcuts are `Depends(_check)` objects — do not wrap in additional `Depends()`

---

## 7. Domain Exception Pattern

Services raise HTTP-agnostic exceptions:
- `NotFoundError` → 404
- `ConflictError` → 409
- `DomainPermissionError` → 403
- `DomainError` → 409

Route functions let these propagate; `main.py` maps them.

---

## 8. Test Coverage

- **1,198 tests passing** (2026-07-12)
- 33 test files
- Coverage includes: auth, institutions, faculties, departments, programmes, modules, files, audits, workflow, approvals, reporting, knowledge pipeline, AI agents
- 8 warnings (non-fatal deprecation notices)
- 0 failures, 0 errors

**Assessment:** Strong unit/integration coverage. Tests are the most reliable quality indicator in this codebase.

---

## 9. Known Backend Bugs (Fixed — Do Not Revert)

1. **`Faculty.__tablename__`**: Explicit `"faculties"` in `backend/app/models/faculty.py`
2. **Double-wrapped `Depends()`**: All 7 audit route files use role guards as direct default values
3. **`run_status.value`**: `audits.py` line ~225 uses string interpolation directly on `run_status` (stored as plain `str`, not enum)
4. **`AuditRunBrief` nullable fields**: `module_id` and `programme_id` are `uuid.UUID | None` — making either non-nullable crashes `GET /audits` for mixed run types

---

## 10. Open Backend Issues

1. **`GET /api/v1/audits` returns empty list**: Global audit list endpoint returns 0 results despite completed audit runs existing. Root cause: likely a tenant scoping or JOIN issue in `audits.py`. The per-module path (`GET /api/v1/audits/modules/{id}/latest`) works correctly.
2. **`GET /api/v1/knowledge-search` → 405**: Method not allowed. Either wrong HTTP verb required, or route not mounted correctly.
3. **`GET /api/v1/qualification/search` → 404**: Route does not exist or is not mounted.
4. **`GET /api/v1/findings` → 404**: No dedicated findings list route found. Findings appear to only be accessible via audit results.
5. **Placeholder embeddings**: AI assistant returns `is_placeholder_mode: true` — Qdrant is populated with hash-based vectors, not real semantic embeddings. Real AI provider is called for generation but retrieval is not semantically relevant.
