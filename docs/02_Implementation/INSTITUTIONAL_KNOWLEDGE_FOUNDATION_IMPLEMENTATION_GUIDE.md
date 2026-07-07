# Institutional Knowledge Foundation — Implementation Guide

## Backend

### Models
New files in `backend/app/models/`: `campus.py`, `school.py`,
`institution_qualification.py` (class `Qualification`, table `qualifications` —
named to avoid clashing with the existing `qualification.py` /
`QualificationRecord`), `learning_outcome.py`, `graduate_attribute.py`,
`policy.py`, `institution_document.py`, `accreditation.py`, `contact.py`.

Back-references added to `institution.py`, `faculty.py`, `department.py`
(`school_id`), `programme.py`, `module.py`. All registered in
`app/models/__init__.py`.

### Migration
`alembic/versions/20260707_0000_b2c3d4e5f6a7_add_institutional_knowledge_foundation.py`
- `down_revision = "f7a8b9c0d1e2"` (Split-1 institution-registry migration).
- Creates 11 tables and adds `departments.school_id`.
- Raw `op.create_table` calls (no model imports).

```bash
cd backend
python -m alembic upgrade head
```

### API + schemas
- `app/schemas/institution_knowledge.py` — Pydantic response models.
- `app/routes/institution_knowledge.py` — 6 endpoints, registered in `main.py`.

## Data package + seed

`database/seed_data/institution_knowledge_foundation/*.json` (15 files).
Regenerate with the generator approach documented in the package README.

```bash
cd backend
python ../database/seed_data/seed_institution_knowledge_foundation.py
# or the full pipeline:
python ../database/seed_data/run_all.py
```

Natural keys per entity are documented inline in the seed script. The seed is
idempotent and provenance-safe.

## Frontend

- `src/lib/api/institutionKnowledge.ts` — typed API client.
- `src/hooks/useInstitutionKnowledge.ts` — React Query hooks.
- `src/app/(main)/knowledge/foundation/page.tsx` — coverage dashboard.
- `src/app/(main)/institution/profile/page.tsx` — profile page.
- `src/lib/rbac.ts` — added `/knowledge/foundation` and `/institution/profile`
  (STAFF).

## Gotchas
- ShadCN here uses `@base-ui/react` — no `asChild`; use `buttonVariants`+`Link`.
- Never double-wrap `AdminRequired` / `AnyAuthenticatedUser` in `Depends()`.
- `run_status` is a plain `str`.
