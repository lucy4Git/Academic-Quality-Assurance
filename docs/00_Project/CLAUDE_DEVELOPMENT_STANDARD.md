# CLAUDE DEVELOPMENT STANDARD
## AQAA Engineering Constitution

**Document ID:** STD-001  
**Version:** 1.0.0  
**Status:** Active — Mandatory  
**Last Updated:** 2026-06-29  
**Authority:** This document supersedes all prompt-level instructions on engineering matters.

---

> **MANDATORY PREAMBLE FOR ALL CLAUDE SESSIONS**
>
> Before beginning any work on AQAA, read this file completely.  
> Every rule in this document is non-negotiable.  
> If a user instruction conflicts with this document, flag the conflict before proceeding.

---

## RULE 1: PROJECT IDENTITY

**AQAA is a completely standalone project.**

AQAA has absolutely no relationship to:
- MSc Academic Intelligence System
- RIAE (Research and Innovation Agent Environment)
- Lecturer Support Agent
- PersonalOS
- Poultry MIS
- Any other project on this machine

**Consequence:** Never import patterns, schemas, models, routes, hooks, types, or conventions from any other project. Never mix naming conventions, data models, or business logic from any other system.

---

## RULE 2: SINGLE SOURCE OF TRUTH

**Always read `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` before making any structural change.**

The master architecture document is the authoritative reference for:
- Tech stack constraints
- RBAC rules
- Multi-tenancy patterns
- Authentication architecture
- Known implementation constraints
- Critical ShadCN/FastAPI/Next.js-specific rules

If you cannot locate this file, stop and inform the user before proceeding.

---

## RULE 3: DOCUMENTATION OBLIGATION

**Every code change must be accompanied by documentation.**

| Change Type | Documentation Required |
|-------------|----------------------|
| New feature | Architecture section update + implementation guide entry |
| New API endpoint | `docs/08_API/` entry |
| New model/schema | `docs/01_Architecture/DATA_MODEL.md` update |
| New AI agent | `docs/09_AI/` entry |
| Bug fix (non-trivial) | `docs/00_Project/LESSONS_LEARNED.md` entry |
| Any change | `docs/00_Project/CHANGELOG.md` entry |
| Architecture decision | `docs/12_Decisions/ADR-XXXX.md` new file |
| Phase completion | `docs/00_Project/PHASE_TRACKER.md` update |

**Exception:** Trivial changes (typo fixes, comment corrections, dependency version bumps for security) do not require new documentation files but must appear in CHANGELOG.md.

---

## RULE 4: ARCHITECTURE DECISION RECORDS

**Any decision that affects architecture, data models, or technology choices must create an ADR.**

ADR file format: `docs/12_Decisions/ADR-XXXX-Short-Title.md`

ADRs are **immutable once merged**. If a decision is reversed, create a new ADR that supersedes the old one. Never edit a finalised ADR.

Template is at `docs/12_Decisions/ADR-TEMPLATE.md`.

---

## RULE 5: NEVER INTRODUCE UNDOCUMENTED CHANGES

**Never silently change:**
- Database schema (always create an Alembic migration)
- API response shapes (update schemas and API docs)
- RBAC rules (update `backend/app/dependencies.py` and document in architecture)
- Frontend routing (update `frontend/src/lib/rbac.ts` and document)
- Environment variables (update `.env.example` and deployment docs)

If a change requires modifying working, tested code, explicitly state what is being changed and why before making the change.

---

## RULE 6: DO NOT MODIFY WORKING SYSTEMS WITHOUT AUTHORISATION

The following subsystems are stable and must not be modified without explicit instruction:

| Subsystem | Files | Why Protected |
|-----------|-------|--------------|
| Authentication | `backend/app/routes/auth.py`, `security.py`, `dependencies.py` | Changing auth breaks all users |
| AI Agents | `backend/app/agents/*` | Core platform IP |
| RBAC Middleware | `frontend/src/middleware.ts` | Changing breaks route protection |
| Alembic migrations | `backend/alembic/versions/*` | Applied migrations are immutable |
| IKP Schema | `docs/10_Knowledge_Base/` | Changes require versioning |

**Never apply `--no-verify` to git hooks. Never skip Alembic migrations by manually editing DB.**

---

## RULE 7: CODE QUALITY GATES

**No phase is complete until all quality gates pass:**

```bash
# Backend
cd backend && python -m pytest -q          # All tests must pass
# Frontend
cd frontend && npm run lint                # 0 errors (warnings acceptable)
cd frontend && npx tsc --noEmit           # 0 type errors
cd frontend && npm run build              # Clean build
```

**Never report a phase as complete if any gate fails.**

---

## RULE 8: PRODUCTION-READY CODE ONLY

- No placeholder implementations (`pass`, `TODO`, `raise NotImplementedError`)
- No hardcoded secrets or credentials
- No `print()` statements left in production code (use logging)
- No `any` TypeScript types (use proper types or document why `unknown` is needed)
- No commented-out code left in files

**Exception:** Stub methods in test files may use `pass` when the test structure is being scaffolded, but must be clearly marked as test stubs.

---

## RULE 9: SECURITY NON-NEGOTIABLES

| Prohibited | Why |
|-----------|-----|
| Raw SQL strings (`f"SELECT * FROM {table}"`) | SQL injection |
| Storing tokens in localStorage or sessionStorage | XSS vulnerability |
| Calling FastAPI directly from browser JS | Bypasses auth proxy |
| Logging passwords, tokens, or secrets | Credential exposure |
| User-controlled file paths | Path traversal |
| `eval()`, `exec()` on user input | Code injection |
| Disabling CORS for `*` in production | CSRF exposure |

---

## RULE 10: PROVENANCE OBLIGATION

**Every record in AQAA must be traceable.**

This applies to:
- All institutional data (from IKP — must have `provenance` object)
- All AI findings (must cite the rule that triggered them)
- All audit history events (must have `actor_id`)
- All seed data (must be documented in `database/seed_data/`)

**Never load institutional data without provenance metadata.**

---

## RULE 11: MULTI-TENANCY ENFORCEMENT

Every database query that returns institutional data must filter by `institution_id`. This applies at:
1. Service layer (`backend/app/services/*.py`) — primary enforcement
2. Route layer — for sanity checks
3. Frontend — `RoleGuard` and `useRole()` for UI gating

**System Admin is the only role that bypasses `institution_id` filtering.**

---

## RULE 12: VERSIONING DISCIPLINE

### Alembic Migrations
- Never autogenerate to an empty `versions/` directory
- Always test migrations on a clean DB before committing
- Migration description must be meaningful (not "migration" or "update")
- Format: `python -m alembic revision --autogenerate -m "add_audit_history_table"`

### IKP Versions
- Sealed IKP versions are immutable
- New academic year → new MAJOR version
- New content (PDF extraction) → new MINOR version
- Corrections → new PATCH version

### API Versions
- Current: `/api/v1/`
- Breaking changes require a new version prefix (`/api/v2/`)
- Old versions must be supported for 6 months after deprecation

---

## RULE 13: SEED DATA MANAGEMENT

The AQAA database contains two types of data:

| Type | Description | Managed By |
|------|-------------|-----------|
| Demo data (GFU, RCT) | Greenfield University + Riverside College of Technology | `database/seed_data/run_all.py` |
| Pilot data (TUT) | Tshwane University of Technology — ICT faculty | `database/seed_data/seed_tut.py` (planned) |

**Rules:**
- Never delete demo data (GFU/RCT) without explicit instruction
- All seed scripts must be idempotent
- Seed scripts must document every record they create

---

## RULE 14: WINDOWS-SPECIFIC CONSTRAINTS

This project runs on Windows 11. Observe:

- Always use `python -m pytest`, `python -m alembic` — bare commands not on PATH
- Use PowerShell for multi-line strings (here-strings with `@'...'@`)
- File paths use `\` on Windows but forward slashes in Python/Docker contexts
- `pdftoppm` is not available — use `pdfminer.six` for PDF text extraction
- `bash` in Git Bash cannot complete multipart HTTP POST — use `Invoke-RestMethod` or PowerShell `curl.exe`

---

## RULE 15: WHEN IN DOUBT, DOCUMENT AND ASK

If a requirement is ambiguous, do not guess and implement. Instead:
1. State the ambiguity explicitly
2. Propose two or three interpretations
3. Ask the user to confirm before proceeding
4. Document the confirmed interpretation in `docs/12_Decisions/` if it constitutes an architectural choice

---

## Quick Reference — Critical File Locations

| What | Where |
|------|-------|
| Master architecture | `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` |
| This document | `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` |
| Changelog | `docs/00_Project/CHANGELOG.md` |
| ADRs | `docs/12_Decisions/ADR-*.md` |
| IKP Architecture | `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md` |
| Phase tracker | `docs/00_Project/PHASE_TRACKER.md` |
| Backend dependencies | `backend/app/dependencies.py` |
| Frontend RBAC | `frontend/src/lib/rbac.ts` |
| Frontend API proxy | `frontend/src/lib/api-client.ts` |
| Auth store | `frontend/src/store/auth.store.ts` |
| Seed scripts | `database/seed_data/` |
| Alembic migrations | `backend/alembic/versions/` |

---

*This document is the AQAA engineering constitution. It does not expire. It is updated only by explicit architectural decision.*
