# AQAA Release Candidate 1.0 — Report

**Document ID:** RC-001  
**Version:** 1.0.0-rc4  
**Date:** 2026-07-04  
**Status:** Release Candidate — Ready for Deployment Preparation  
**Classification:** Internal

---

## Executive Summary

AQAA Release Candidate 1.0 is a complete, functional Academic Quality Assurance platform serving TUT and UP as active pilot institutions. All planned sprint deliverables are implemented, tested, and passing quality gates. The system is ready for deployment preparation (secret audit, infrastructure provisioning, and go-live coordination).

---

## Platform Status

| Dimension | Status | Detail |
|-----------|--------|--------|
| Backend tests | ✅ 884 passing | 11.84s, 0 failures |
| TypeScript | ✅ 0 errors | `npx tsc --noEmit` clean |
| ESLint | ✅ 0 warnings | `npm run lint` clean |
| Production build | ✅ Clean | `npm run build` succeeds |
| Tenant isolation | ✅ Verified | TUT/UP isolated; GFU/RCT archived |
| Auth & RBAC | ✅ Working | 7 roles, httpOnly JWT cookies |
| AI provider | ✅ Configured | LOCAL_DEV default; OpenAI/Anthropic/Ollama supported |

---

## Implemented Subsystems

### Core Platform
| Subsystem | Endpoints | Status |
|-----------|-----------|--------|
| Authentication & RBAC | 4 | ✅ |
| Institution Management | 8 | ✅ |
| Faculty Management | 6 | ✅ |
| Department Management | 6 | ✅ |
| Programme Management | 8 | ✅ |
| Module Management | 8 | ✅ |
| User Management | 6 | ✅ |

### Quality Assurance
| Subsystem | Endpoints | Status |
|-----------|-----------|--------|
| File Upload & Library | 6 | ✅ |
| Module Folder Audit Agent | 3 | ✅ |
| Assessment Compliance Agent | 3 | ✅ |
| Moderation Compliance Agent | 3 | ✅ |
| Attendance Compliance Agent | 3 | ✅ |
| Evidence Verification Agent | 3 | ✅ |
| Outcome Alignment Agent | 3 | ✅ |
| Accreditation Readiness Agent | 3 | ✅ |
| Programme Review Agent | 3 | ✅ |
| Workflow Automation | 9 | ✅ |
| Comments | 4 | ✅ |
| Notifications | 5 | ✅ |
| Approvals | 4 | ✅ |

### Knowledge & AI
| Subsystem | Endpoints | Status |
|-----------|-----------|--------|
| ADIP Document Processing | 5 | ✅ |
| IKP Management | 8 | ✅ |
| Knowledge Review | 11 | ✅ |
| Knowledge Search (Qdrant) | 3 | ✅ |
| AI QA Assistant | 12 | ✅ |
| AI Provider Layer | — | ✅ OpenAI/Anthropic/Ollama/LOCAL_DEV |
| Chat Sessions | 5 | ✅ |
| Provider Status Verification | 1 | ✅ |

### Intelligence & Analytics
| Subsystem | Endpoints | Status |
|-----------|-----------|--------|
| Qualification Intelligence | 6 | ✅ |
| Reporting & Analytics | 9 | ✅ |
| Export (CSV/Excel) | 2 | ✅ |
| Dashboard | 1 | ✅ |

---

## Active Pilot Institutions

| Institution | Code | Type | Status |
|-------------|------|------|--------|
| Tshwane University of Technology | TUT | Active Pilot | ✅ Live |
| University of Pretoria | UP | Active Pilot | ✅ Live |
| Gqeberha Further Education (demo) | GFU | Archived | 🔒 Archived |
| Rondebosch College of Technology (demo) | RCT | Archived | 🔒 Archived |

---

## Seeded Dataset (for pilot)

All seeded users share password `ChangeMe123!` — must be changed before production go-live.

| Entity | Count |
|--------|-------|
| Institutions | 4 (2 active, 2 archived) |
| Faculties | 8 |
| Departments | 16 |
| Programmes | 16 |
| Modules | 48 |
| Lecturers | 48 |
| QA Officers | 4 |
| Students | 30 |

---

## Test Counts by Area

| Area | Tests |
|------|-------|
| Auth & security | 38 |
| Institutions, hierarchy | 45 |
| Pilot access control | 38 |
| Archive filter | 25 |
| Workflow & approvals | 40 |
| Knowledge indexing | 46 |
| Knowledge review | 42 |
| IKP management | 42 |
| AI QA Assistant | 38 |
| AI Provider layer | 35 |
| Reporting & exports | 28 |
| Qualification Intelligence | 39 |
| Tenant isolation | 59 |
| Other / integration | 369 |
| **Total** | **884** |

---

## Database Migrations Applied

| Revision | Description |
|----------|-------------|
| `99c7b97c9a76` | Initial schema |
| `bcb42a8b6462` | Programme QA fields |
| `6bcc7db53782` | Module audit tables |
| `a1afe7223e2a` | Audit evidence table |
| `146ff3d10cd9` | Audit history table |
| `2a7b17360d01` | Workflow, comments, notifications |
| `7c5db84357e3` | ADIP registry tables |
| `b0df78d4b8ec` | Knowledge review tables |
| `a1b2c3d4e5f6` | Institution is_active flag |
| `c4d5e6f7a8b9` | AI chat session tables |
| `d5e6f7a8b9c0` | Qualification records table |

---

## Known Limitations (pre-deployment)

1. **PDF export** — Full PDF (reportlab) not yet enabled. Export returns structured plain-text with clear notice. CSV and Excel export are fully implemented.
2. **AI provider keys** — `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` must be configured in production `.env` before enabling real AI responses. System falls back safely to LOCAL_DEV.
3. **Seed passwords** — All seeded user accounts use `ChangeMe123!`. These must be reset before go-live.
4. **SECRET_KEY** — Must be replaced with a cryptographically strong random key in production.
5. **CORS origins** — `CORS_ORIGINS` must be updated to the production frontend domain.
6. **Qdrant persistence** — Qdrant vector data is volume-mounted in Docker. Backup strategy needed before go-live.

---

## Pre-Deployment Blockers

None. All quality gates pass. Secret masking and GitHub safety audit are the next step per sprint instructions.

---

## Recommended Next Steps

1. **Secret audit** — Run GitHub secret scan; mask/rotate any exposed credentials.
2. **Infrastructure provisioning** — Configure production PostgreSQL, Redis, Qdrant.
3. **Environment configuration** — Set `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, AI provider keys.
4. **Password reset** — Force-reset all seeded user passwords.
5. **SSL/TLS** — Configure HTTPS termination (nginx/traefik).
6. **Monitoring** — Set up health check probes (`GET /health`), log aggregation.
7. **Backups** — Schedule PostgreSQL and Qdrant backups.
8. **Go-live coordination** — Brief TUT and UP pilot users.
