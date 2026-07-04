# Reference Documentation

Quick reference cards for AQAA developers and operators.

## Contents

| Document | Status |
|----------|--------|
| `NQF_REFERENCE.md` | ⏳ Planned — South African NQF framework levels and credit standards |
| `RBAC_MATRIX.md` | ⏳ Planned — Full permission matrix by role |
| `ERROR_CODES.md` | ⏳ Planned — All API error codes and meanings |
| `ENUM_VALUES.md` | ⏳ Planned — All enum values used in the system |
| `CHECKLIST_ITEMS.md` | ⏳ Planned — The 10 QA checklist items with descriptions |
| `WORKFLOW_STATES.md` | ⏳ Planned — 9 workflow states and allowed transitions |
| `CONFIDENCE_THRESHOLDS.md` | ⏳ Planned — IKP confidence score reference |
| `GLOSSARY.md` | ⏳ Planned — Domain terminology (NQF, APS, CHE, DHET, SAQA, WIL, RPL) |

## Quick Reference: Key File Paths

| What | Path |
|------|------|
| Backend dependencies | `backend/requirements.txt` |
| Frontend dependencies | `frontend/package.json` |
| Alembic migrations | `backend/alembic/versions/` |
| Seed scripts | `database/seed_data/` |
| AI agents | `backend/app/agents/` |
| FastAPI dependencies | `backend/app/dependencies.py` |
| Frontend RBAC | `frontend/src/lib/rbac.ts` |
| Frontend API client | `frontend/src/lib/api-client.ts` |
| Auth store | `frontend/src/store/auth.store.ts` |
| IKP packages | `ikp/institutions/` |
