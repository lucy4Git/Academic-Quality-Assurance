# API Documentation

This section documents all AQAA API endpoints.

## Base URL

- **Development:** `http://localhost:8000/api/v1/`
- **Swagger UI:** `http://localhost:8000/api/v1/docs`
- **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`
- **Frontend proxy:** All frontend calls go through `/api/proxy/{path}`

## Authentication

All endpoints (except `/auth/token` and `/auth/login`) require a Bearer token.  
In the frontend, the token is read from the `access_token` httpOnly cookie by the Next.js proxy.  
In Swagger UI, use the "Authorize" button with username/password (form fields).

## Endpoint Index

| Group | Prefix | Description |
|-------|--------|-------------|
| Authentication | `/auth` | Login, refresh, profile |
| Institutions | `/institutions` | Institution CRUD |
| Faculties | `/faculties` | Faculty CRUD |
| Departments | `/departments` | Department CRUD |
| Programmes | `/programmes` | Programme CRUD |
| Modules | `/modules` | Module CRUD |
| Module Audits | `/audits`, `/module-audits` | Manual QA audit engine |
| Evidence | `/evidence` | Evidence upload, download, preview |
| AI Agents | `/audits`, `/assessment-audits`, etc. | 8 AI audit agents |
| Workflow | `/workflow` | Audit workflow management |
| Comments | `/comments` | Audit comments |
| Notifications | `/notifications` | In-app notifications |
| Approvals | `/approvals` | QA approval actions |
| Dashboard | `/dashboard` | Entity count summaries |
| Files | `/files` | File library |

## API Conventions

- **List endpoints:** Return arrays, support `skip` and `limit` query params
- **Error format:** `{"detail": "Error message"}` (FastAPI default)
- **HTTP status codes:** 200 (read), 201 (create), 204 (delete), 202 (async trigger), 400/403/404/409 (errors)
- **AI agent triggers:** Always return 202 with `{"run_id": "..."}` — poll `/audits/{run_id}` for status

## Contents

| Document | Status |
|----------|--------|
| `AUTH_API.md` | ⏳ Planned |
| `INSTITUTION_HIERARCHY_API.md` | ⏳ Planned |
| `AUDIT_ENGINE_API.md` | ⏳ Planned |
| `EVIDENCE_API.md` | ⏳ Planned |
| `WORKFLOW_API.md` | ⏳ Planned |
| `AI_AGENTS_API.md` | ⏳ Planned |
