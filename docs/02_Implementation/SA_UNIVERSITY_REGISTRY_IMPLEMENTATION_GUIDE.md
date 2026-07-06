# SA University Registry — Implementation Guide

**Document ID:** IMPL-SA-REG-001
**Status:** Active
**Introduced:** Split 1 (2026-07-06)

---

## What was implemented

1. Registry data files under `database/seed_data/institution_registry/`.
2. Six provenance columns on the `Institution` model.
3. Alembic migration `f7a8b9c0d1e2`.
4. `InstitutionRead` schema fields.
5. `seed_sa_universities.py` seed + `run_all.py` integration.
6. Tests in `backend/tests/test_split1_sa_registry.py`.

## Files touched

| File | Change |
|------|--------|
| `backend/app/models/institution.py` | Added `province`, `website`, `source_url`, `data_status`, `data_confidence`, `is_demo`; imported `Float`. |
| `backend/app/schemas/institution.py` | Added the six optional fields to `InstitutionRead`. |
| `backend/alembic/versions/20260706_0000_f7a8b9c0d1e2_add_institution_registry_fields.py` | New migration. |
| `database/seed_data/seed_sa_universities.py` | New idempotent seed. |
| `database/seed_data/run_all.py` | Added step 4/4. |
| `database/seed_data/institution_registry/*` | New data + docs. |
| `backend/tests/test_split1_sa_registry.py` | New tests. |

## Applying the change

```bash
# 1. Run the migration (requires the datastores running)
cd backend
python -m alembic upgrade head          # applies f7a8b9c0d1e2

# 2. Seed the 26 university profiles (idempotent)
python ../database/seed_data/seed_sa_universities.py

#    …or run the whole seed pipeline
python ../database/seed_data/run_all.py

# 3. Verify
python -m pytest tests/test_split1_sa_registry.py -q
```

## Migration chain note

The migration head at time of writing was `e6f7a8b9c0d1`
(`add_user_registration_fields`). The revision id `a1b2c3d4e5f6` referenced in
the original plan was **already taken** by
`20260701_1200_a1b2c3d4e5f6_add_institution_is_active.py`, so a fresh revision id
`f7a8b9c0d1e2` was used, chained from the real head. `is_active` was therefore
**not** re-added (it already exists).

## Adding or editing a university

1. Edit `south_africa_public_universities.json` (keep `abbreviation` unique).
2. Ensure `institution_type` is one of `comprehensive`,
   `university_of_technology`, `distance`, `specialised`.
3. Set `country = "South Africa"`, `is_demo = true`.
4. Re-run `seed_sa_universities.py` (idempotent upsert by code).
5. `pytest tests/test_split1_sa_registry.py -q`.

## Guardrails

- Never write real internal QA data for these institutions.
- The seed only writes non-null registry fields on existing rows — it will not
  wipe pilot relationships.
- Keep `is_demo = true` until an institution's *real* QA data is onboarded.
