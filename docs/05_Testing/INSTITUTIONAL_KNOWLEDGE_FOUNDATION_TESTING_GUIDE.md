# Institutional Knowledge Foundation — Testing Guide

## Test file

`backend/tests/test_split2_wave1_foundation.py` (11 tests).

| Test | Verifies |
|------|----------|
| `test_json_files_exist` | All 16 package files present. |
| `test_campuses_json_valid` | Required keys on campus entries. |
| `test_faculties_json_26_institutions` | All 26 institution codes represented. |
| `test_no_customer_data_in_seed_files` | No seed file contains `customer_data`. |
| `test_synthetic_demo_marked_is_synthetic` | `synthetic_demo` ⇒ `is_synthetic=true`. |
| `test_accreditation_bodies_public_verified` | Bodies are `public_verified`. |
| `test_models_importable` | All new models import. |
| `test_campus_model_has_provenance_fields` | `data_status`/`is_synthetic`/`source_url` on model. |
| `test_institution_knowledge_overview_endpoint_requires_admin` | `/overview` gated by `AdminRequired`. |
| `test_institution_knowledge_profile_endpoint_registered` | Profile route registered. |
| `test_router_registered_in_main` | Router included in `main.py`. |

## Running

```bash
cd backend
python -m pytest tests/test_split2_wave1_foundation.py -q     # this subsystem
python -m pytest -q --tb=no                                   # full suite
```

Frontend type check:

```bash
cd frontend
npx tsc --noEmit --skipLibCheck
```

## Migration validation

```bash
cd backend
python -m alembic upgrade head          # apply
python -m alembic downgrade -1          # roll back the foundation migration
```

The migration was validated by offline SQL generation
(`alembic upgrade f7a8b9c0d1e2:b2c3d4e5f6a7 --sql`) producing all 11
`CREATE TABLE` statements plus the `departments.school_id` column and FK.

## Manual smoke test

1. `python ../database/seed_data/seed_institution_knowledge_foundation.py`
2. `GET /api/v1/institution-knowledge/institutions/{id}/coverage` returns counts
   and a provenance breakdown.
3. As a student token, `GET .../profile` returns only public contacts;
   `GET .../coverage` returns 403.
