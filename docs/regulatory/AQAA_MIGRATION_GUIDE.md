# AQAA Regulatory Engine — Migration Guide

**Phase C | Version 1.0 | 2026-07-14**

---

## Migration Chain

| Revision | Description |
|----------|-------------|
| `99c7b97c9a76` | Initial schema (Phase A) |
| `a1b2c3d4e5f7` | Phase C regulatory framework engine |

---

## Applying Migrations

```bash
cd backend
python -m alembic upgrade head
python -m alembic current  # verify: a1b2c3d4e5f7 (head)
```

**Important:** Always run migrations from the host machine, not from inside the Docker container. The `./backend` directory is mounted at `/app` but `database/` is not — seed scripts must run from the host.

---

## Phase C Migration (`a1b2c3d4e5f7`)

Creates 12 new tables:

1. `regulatory_authorities`
2. `quality_frameworks`
3. `framework_versions`
4. `framework_applicability_rules`
5. `framework_standards`
6. `framework_criteria`
7. `evidence_requirements`
8. `evidence_criterion_mappings`
9. `framework_assessment_runs`
10. `criterion_assessment_results`
11. `cross_framework_mappings`
12. `regulatory_findings`

Also adds FK columns to `audit_findings`:
- `framework_version_id`
- `criterion_id`
- `evidence_requirement_id`
- `criterion_assessment_result_id`

---

## Rolling Back

```bash
python -m alembic downgrade -1  # rolls back Phase C tables
```

**Warning:** Downgrading drops all 12 Phase C tables and their data. This is irreversible without a backup.

---

## Generating New Migrations

```bash
python -m alembic revision --autogenerate -m "description"
python -m alembic upgrade head
```

Ensure the previous migration (`a1b2c3d4e5f7`) is applied before generating a new one:
```bash
python -m alembic current
# should show: a1b2c3d4e5f7 (head)
```

Never generate a migration with an empty `alembic/versions/` directory.

---

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `alembic: command not found` | Console scripts not on PATH | Use `python -m alembic` |
| `Target database is not up to date` | Pending migration | `python -m alembic upgrade head` |
| `Can't locate revision identified by '...'` | Migration file missing | Restore from git |
| `table already exists` | Migration applied twice | `python -m alembic stamp head` |
