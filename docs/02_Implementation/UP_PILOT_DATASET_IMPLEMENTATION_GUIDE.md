# UP Pilot Dataset — Implementation Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Scope:** University of Pretoria pilot institution in AQAA

---

## Overview

This guide documents the University of Pretoria (UP) pilot institution dataset
added during Phase 5.5. The UP pilot is scoped to the Faculty of Engineering,
Built Environment and Information Technology (EBIT), covering three
departments: Computer Science, Informatics, and Information Science.

---

## IKP Location

```
ikp/institutions/up/2026/v1.0.0/
├── package.json                    ← IKP metadata and version
├── source_registry.json            ← Document provenance registry
├── institution.json                ← Institution-level data
├── campuses.json                   ← Campus locations (5 campuses)
├── faculties.json                  ← 10 faculties; EBIT has pilot_scope: true
├── departments.json                ← 7 EBIT depts; CS/INF/IS have pilot_scope: true
├── programmes.json                 ← 10 programmes (BSc CS, BCom Inf, BIS + honours/postgrad)
├── modules.json                    ← 15 modules (COS/INF codes)
├── admission_requirements.json     ← BSc CS, BCom Inf, BIS entry requirements
├── provenance_index.json           ← Field-level source citations
├── extraction_summary.json         ← Extraction confidence report
└── ai/
    ├── knowledge_chunks.json       ← 27 AI-ready chunks (vector store input)
    ├── retrieval_index_manifest.json ← Qdrant collection: up_2026_v1_0_0
    └── qa_context_summary.json     ← QA officer context summary
```

---

## Seeding UP Data

Prerequisites:
1. Docker datastores running: `docker compose up -d postgres redis qdrant`
2. Migrations applied: `cd backend && python -m alembic upgrade head`

Run the seed script from the repo root:

```bash
python database/seed_data/seed_up.py
```

Expected output:

```
[UP SEED] Institution UP already exists (id=...)
[UP SEED] Loading 7 departments from IKP...
[UP SEED] Loading 10 programmes from IKP...
[UP SEED] Loading 15 modules from IKP...
[UP SEED] Done. 3 depts | 10 programmes | 15 modules
```

The script is idempotent — re-running is safe.

---

## Pilot Scope

| Pilot | Dept Code | Dept Name | Programmes | Modules |
|-------|-----------|-----------|------------|---------|
| Yes | CS | Computer Science | BSc CS, BSc CS Ext, BSc CS Hons, MSc CS, PhD CS | COS110, COS132, COS212, COS220, COS301, COS326, COS330, COS332, COS344, COS352, COS360, COS365 |
| Yes | INF | Informatics | BCom Inf, BCom Inf Hons, MIT | INF154, INF263 |
| Yes | IS | Information Science | BIS, BIS Hons | INF370 |

---

## Institution Record

| Field | Value |
|-------|-------|
| Code | UP |
| Name | University of Pretoria |
| Country | South Africa |
| Type | pilot |
| is_active | true |
| Alembic migration | a1b2c3d4e5f6 |

---

## Data Quality Notes

- All IKP fields carry `provenance` (source document + page) and `confidence` scores
- Fields marked `pending_verification` are stored as `NULL` in the database
  (the `_field_value()` helper in `seed_up.py` returns `None` for these)
- The `extraction_summary.json` reports overall confidence and pending field count

---

## Tenant Isolation

UP data is fully isolated from TUT data at the database level via `institution_id`
foreign keys. See `backend/app/dependencies.py:assert_institution_access()` and
`backend/tests/test_tenant_isolation.py` for verification.

---

## Next Steps

1. Load 27 AI chunks into Qdrant collection `up_2026_v1_0_0`
2. Seed UP pilot test users (QA officer, lecturer)
3. Run Module Folder Audit on a UP COS module
