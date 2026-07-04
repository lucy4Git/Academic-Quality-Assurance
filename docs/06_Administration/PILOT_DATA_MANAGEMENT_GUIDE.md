# Pilot Data Management Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Audience:** System Administrators and Engineering

---

## Overview

AQAA runs two active pilot institutions alongside two archived demo institutions:

| Institution | Code | Status | Type | Users |
|---|---|---|---|---|
| Tshwane University of Technology | TUT | Active | pilot | 6 pilot |
| University of Pretoria | UP | Active | pilot | 6 pilot |
| Greenfield University | GFU | Archived | demo | 40 (inactive) |
| Riverside College of Technology | RCT | Archived | demo | 42 (inactive) |

GFU and RCT are **historical demo data only**. They are never deleted — only archived (`is_active=False`, `institution_type='demo'`). All GFU/RCT users have `is_active=False` and cannot log in.

---

## Current Academic Dataset

### TUT — Tshwane University of Technology

IKP source: `ikp/institutions/tut/2026/v1.1.0/approved/`

| Entity | Count | Notes |
|---|---|---|
| Faculties | 1 | FICT — Faculty of Information and Communication Technology |
| Departments | 4 | CS, CSE, INF, IT |
| Programmes | 22 | All ICT programmes from TUT Yearbook 2026 |
| Modules | 174 | All ICT modules from TUT Yearbook 2026 |

### UP — University of Pretoria

IKP source: `ikp/institutions/up/2026/v1.0.0/`

**Pilot scope** (by design): CS, Informatics, and Information Science programmes only.

| Entity | Count | Notes |
|---|---|---|
| Faculties | 1 | EBIT — Faculty of Engineering, Built Environment and IT |
| Departments | 7 | All EBIT departments created; 3 have programme data |
| Programmes | 10 | CS (5), Informatics (3), Information Science (2) |
| Modules | 15 | COS modules (BSc CS) + INF modules (BCom Informatics) |

**UP programme code table:**

| Entity key | DB code | Programme name |
|---|---|---|
| UP-EBIT-CS-BSC | 02130105 | BSc (Computer Science) |
| UP-EBIT-CS-BSC-EXT | BSC-EXT-CS | BSc (Computer Science) Extended Programme |
| UP-EBIT-CS-BSC-HONS | BSC-HONS-CS | BSc Hons (Computer Science) |
| UP-EBIT-CS-MSC | MSC-CS | MSc (Computer Science) |
| UP-EBIT-CS-PHD | PHD-CS | PhD (Computer Science) |
| UP-EBIT-INF-BCOM | BCOM-INF | BCom (Informatics) |
| UP-EBIT-INF-BCOM-HONS | BCOM-HONS-INF | BCom Hons (Informatics) |
| UP-EBIT-INF-MIT | MIT-INF | MIT (Master of Information Technology) |
| UP-EBIT-IS-BIS | BIS-IS | BIS (Bachelor of Information Science) |
| UP-EBIT-IS-BIS-HONS | BIS-HONS-IS | BIS Hons (Information Science) |

> **Code derivation rule**: When the IKP `qualification_code` is `pending_verification`, codes are derived from the entity_key suffix: `UP-EBIT-{DEPT}-{QUAL-PARTS}` → `{QUAL-PARTS}-{DEPT}`. The BSc CS code `02130105` is the verified SAQA qualification code.

---

## Seed Scripts

All scripts are idempotent and safe to re-run.

### Full pilot setup (run from repo root)

```bash
# 1. Ensure database is migrated
cd backend && python -m alembic upgrade head

# 2. Seed TUT academic data
python database/seed_data/seed_tut.py

# 3. Seed UP academic data
python database/seed_data/seed_up.py

# 4. Create pilot users (6 per institution)
python database/seed_data/seed_pilot_users.py

# 5. Deactivate all demo users
python database/seed_data/deactivate_demo_users.py
```

### Safe pre-flight check

```bash
python database/seed_data/deactivate_demo_users.py --dry-run
```

### Repair UP programme codes

If UP programme codes become garbled (e.g. after schema changes), re-running
`seed_up.py` will repair them — the update path now sets `code` on existing
records.

---

## Vector Indexing (Qdrant)

After seeding institutional data, index the IKP knowledge chunks into Qdrant for semantic search.

### Index all pilot institutions (from repo root)

```bash
cd backend
python -m app.knowledge_indexing.index_ikp_chunks --all
```

### Index individual institutions

```bash
python -m app.knowledge_indexing.index_ikp_chunks --institution TUT --year 2026 --version v1.1.0
python -m app.knowledge_indexing.index_ikp_chunks --institution UP  --year 2026 --version v1.0.0
```

### Rebuild collections from scratch

```bash
python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate
```

### Expected collections after indexing

| Collection | Institution | Chunks | Dimensions |
|---|---|---|---|
| `tut_2026_v1_1_0` | TUT | 196 | 384 |
| `up_2026_v1_0_0` | UP | 28 | 384 |

**Note:** Development placeholder embeddings are used by default. Vectors are
hash-derived and do not reflect semantic meaning. Replace `EmbeddingService`
in `backend/app/knowledge_indexing/embedding_service.py` with a real model
(e.g. `sentence-transformers/all-MiniLM-L6-v2`) for production.

### Check index status

```
GET /api/v1/knowledge-index/status   (requires QA Officer or above)
```

---

## Archive Filter Behaviour

All list endpoints (`/faculties`, `/departments`, `/programmes`, `/modules`,
`/institutions`) default to `include_archived=false`. For System Admin:

- **Default view** (no query param): active pilot institutions only (TUT, UP).
- **`?include_archived=true`**: all institutions including GFU/RCT demo data.

Non-admin users are always scoped to their own institution; `include_archived`
has no effect for them.

### Frontend

The Institutions list page (System Admin) automatically separates:
- **Active Pilot Institutions** — TUT, UP (shown first)
- **Archived Demo Institutions** — GFU, RCT (shown below with dimmed styling)

All academic hierarchy list pages (Faculties, Departments, Programmes, Modules)
show an **Institution** dropdown for System Admin to filter to a single pilot
institution. The dropdown never includes archived institutions.

---

## Tenant Isolation Rules

| User role | Can see |
|---|---|
| SYSTEM_ADMIN | All active pilot institutions |
| Any other role | Own institution only |
| Inactive user | Cannot log in (401 "account disabled") |

Cross-tenant access raises HTTP 403. This is enforced by `assert_institution_access()`
in `backend/app/dependencies.py` and verified by `tests/test_tenant_isolation.py`
(59 tests) and `tests/test_archive_filter.py` (25 tests).

---

## Adding a New Pilot Institution

1. Create IKP directory: `ikp/institutions/{code}/2026/v1.0.0/`
2. Add JSON files: `institution.json`, `faculties.json`, `departments.json`,
   `programmes.json`, `modules.json`
3. Write `database/seed_data/seed_{code}.py` following the pattern of
   `seed_tut.py` or `seed_up.py`
4. Add a row to `institutions` table with `institution_type='pilot'` and
   `is_active=True`
5. Run `seed_{code}.py` then `seed_pilot_users.py`
6. Update this guide

---

## Known Data Limitations (UP)

The UP IKP v1.0.0 package covers CS, Informatics, and Information Science only.
The remaining four EBIT departments (EECE, Civil, Mechanical, Architecture) have
no programme or module records yet. This is intentional — the UP pilot scope was
agreed with the UP faculty pilot coordinator.

To expand: add data to `ikp/institutions/up/2026/v1.0.0/programmes.json` and
`modules.json`, then re-run `seed_up.py`.
