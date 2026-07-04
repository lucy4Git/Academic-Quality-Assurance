# Testing Documentation

## Test Suite Overview

| Suite | Count | Location | Run Command |
|-------|-------|----------|------------|
| Backend unit + integration | 432 | `backend/tests/` | `cd backend && python -m pytest -q` |
| Frontend type check | 0 errors | Frontend source | `cd frontend && npx tsc --noEmit` |
| Frontend lint | 0 errors | Frontend source | `cd frontend && npm run lint` |
| Frontend build | Clean | Frontend source | `cd frontend && npm run build` |

## Test Quality Standard

All 432 backend tests must pass before any phase is considered complete.  
The test count should only increase — never decrease.

## Test Data

All backend tests use the seeded GFU/RCT demo data.  
Default test password: `ChangeMe123!`  
Test users: see `database/seed_data/README.md`

## Contents

| Document | Status |
|----------|--------|
| `TEST_STRATEGY.md` | ⏳ Planned |
| `BACKEND_TESTING.md` | ⏳ Planned |
| `FRONTEND_TESTING.md` | ⏳ Planned |
| `TENANT_ISOLATION_TESTS.md` | ⏳ Planned |
| `PERFORMANCE_TESTS.md` | ⏳ Planned (Phase 8) |
