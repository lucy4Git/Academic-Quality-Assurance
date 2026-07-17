# AQAA Phase D — Seed Data Snapshot

**Date:** 2026-07-17

---

## Seed Data File

**File:** `database/snapshots/phase-d/aqaa_phase_d_seed_data.sql`
**Size:** ~1.45 MB
**Type:** TEST FIXTURES ONLY — no production or confidential data

---

## Contents

| Table | Rows | Notes |
|-------|------|-------|
| `institutions` | 28 | Test institutions incl. TUT + UP |
| `faculties` | 150 | Test faculties |
| `departments` | 325 | Test departments |
| `programmes` | 748 | NQF levels 5–10 |
| `modules` | 2,327 | With module codes |
| `users` | 95 | All with `ChangeMe123!` password |
| **Total** | **3,673** | |

---

## Excluded Tables

The following tables are NOT included in the seed snapshot:

| Table | Reason |
|-------|--------|
| `files` | Contains uploaded institutional evidence |
| `audit_runs` | Contains run-specific audit data |
| `audit_findings` | Contains finding content from audits |
| `ai_chat_sessions` | Contains conversation history |
| `ai_chat_messages` | Contains message content |
| `ai_artifacts` | Contains generated artifact content |
| `adip_*` tables | Contains institutional document data |
| `downloaded_documents` | Contains downloaded regulatory documents |

---

## Safe Content Confirmation

- No real student records ✅
- No real staff credentials ✅
- No confidential institutional evidence ✅
- No production API keys ✅
- No real examination material ✅
- No real regulatory documents ✅
- All passwords are bcrypt hashes of `ChangeMe123!` ✅

---

## Restore Instructions

### Prerequisites

1. Schema must be applied first:
```bash
cd backend && python -m alembic upgrade head
```

2. Restore seed data:
```bash
docker exec -i aqaa-postgres psql -U aqaa aqaa < database/snapshots/phase-d/aqaa_phase_d_seed_data.sql
```

### Alternative (from host without Docker exec)

```bash
psql -h localhost -U aqaa -d aqaa < database/snapshots/phase-d/aqaa_phase_d_seed_data.sql
```

### Using the project seed runner (recommended)

```bash
cd backend
python ../database/seed_data/run_all.py
```

The project seed runner is idempotent and safe to re-run.

---

## Validation

After restore, verify:
```bash
docker exec aqaa-postgres psql -U aqaa -c "SELECT COUNT(*) FROM institutions;"
# Expected: 28

docker exec aqaa-postgres psql -U aqaa -c "SELECT COUNT(*) FROM users;"
# Expected: 95

docker exec aqaa-postgres psql -U aqaa -c "SELECT COUNT(*) FROM modules;"
# Expected: 2327
```

---

## Seed Manifest

See `database/snapshots/phase-d/aqaa_phase_d_seed_manifest.json` for full manifest including test account credentials.

---

**Status: SAFE — no confidential data included.**
