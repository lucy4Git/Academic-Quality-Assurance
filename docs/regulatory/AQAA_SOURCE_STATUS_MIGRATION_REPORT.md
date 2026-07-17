# AQAA Source Status Migration Report

**Phase C Closure Gate | 2026-07-14**

---

## Purpose

Adds a persisted `source_status` field to the three regulatory provenance tables,
replacing the previous name-based heuristic (`[TEST FIXTURE]` substring in name).

---

## Problem with Name-Based Detection

The prior `is_test_fixture` computed field (`@computed_field @property`) detected
test data by checking `"[TEST FIXTURE]" in name`. This had two weaknesses:

1. Authoritative data imported from official sources with `[TEST FIXTURE]` in its
   name would be incorrectly flagged
2. Test data that had its name edited would silently lose its fixture flag
3. The status was not queryable from the DB — you could not filter or aggregate
   by source provenance without fetching all rows

---

## Solution

`source_status VARCHAR(40) NOT NULL DEFAULT 'TEST_FIXTURE'` added to:

| Table | Column |
|-------|--------|
| `regulatory_authorities` | `source_status` |
| `quality_frameworks` | `source_status` |
| `framework_versions` | `source_status` |

---

## Enum Values

| Value | Meaning |
|-------|---------|
| `OFFICIAL_VERIFIED` | Sourced from official regulatory body; human-verified against source document |
| `OFFICIAL_UNVERIFIED` | Imported from official source but not yet human-verified |
| `INSTITUTIONAL_APPROVED` | Created by the institution and approved by their QA Officer |
| `TEST_FIXTURE` | Test data — do not use for compliance decisions |
| `DRAFT_IMPORT` | Imported via bulk import; pending review |
| `SUPERSEDED` | Replaced by a newer version; retained for audit trail |
| `ARCHIVED` | Retired; no longer applicable |

---

## Migration

**File:** `backend/alembic/versions/20260714_0933_51694630069f_add_source_status_to_regulatory_tables.py`
**Revision:** `51694630069f`
**Revises:** `a1b2c3d4e5f7`

**Safe migration pattern:**
```sql
-- Step 1: Add nullable column (zero-downtime)
ALTER TABLE regulatory_authorities ADD COLUMN source_status VARCHAR(40);
ALTER TABLE quality_frameworks ADD COLUMN source_status VARCHAR(40);
ALTER TABLE framework_versions ADD COLUMN source_status VARCHAR(40);

-- Step 2: Backfill all existing rows
UPDATE regulatory_authorities SET source_status = 'TEST_FIXTURE' WHERE source_status IS NULL;
UPDATE quality_frameworks      SET source_status = 'TEST_FIXTURE' WHERE source_status IS NULL;
UPDATE framework_versions      SET source_status = 'TEST_FIXTURE' WHERE source_status IS NULL;

-- Step 3: Set NOT NULL constraint
ALTER TABLE regulatory_authorities ALTER COLUMN source_status SET NOT NULL;
ALTER TABLE quality_frameworks      ALTER COLUMN source_status SET NOT NULL;
ALTER TABLE framework_versions      ALTER COLUMN source_status SET NOT NULL;
```

---

## Backfill Result

All pre-existing regulatory fixture records seeded by `seed_regulatory_framework.py`
were backfilled to `TEST_FIXTURE`. This matches their names which all begin with
`[TEST FIXTURE]`, so the computed `is_test_fixture` property and the persisted
`source_status` field are consistent.

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/models/enums.py` | Added `SourceStatus` enum (7 values) |
| `backend/app/models/regulatory_authority.py` | Added `source_status` column |
| `backend/app/models/quality_framework.py` | Added `source_status` column |
| `backend/app/models/framework_version.py` | Added `source_status` column |
| `backend/app/schemas/regulatory.py` | `source_status: str` in all 3 Read schemas |
| `database/seed_data/seed_regulatory_framework.py` | Explicit `'TEST_FIXTURE'` in INSERT |
| `frontend/src/lib/api/regulatoryFramework.ts` | `source_status: string` in 3 interfaces |
| `frontend/src/app/(main)/framework-management/FrameworkManagement.tsx` | Emerald badge for non-TEST_FIXTURE |

---

## Frontend Display Logic

| `source_status` | Badge shown |
|----------------|------------|
| `TEST_FIXTURE` | Amber "TEST FIXTURE" badge (from `is_test_fixture` computed field) |
| Any other value | Emerald badge with readable label (e.g. "OFFICIAL VERIFIED") |
| `TEST_FIXTURE` | No emerald badge (amber badge is sufficient) |

---

## How to Promote a Fixture to Official Status

Via the API (when a QA Officer imports authoritative text):

```bash
PATCH /api/v1/regulatory-authorities/{id}
{ "source_status": "OFFICIAL_VERIFIED" }
```

This requires the `QAOfficerRequired` role and removes the TEST FIXTURE caveat
from all AI responses that cite that authority.
