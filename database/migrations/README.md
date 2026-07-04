# AQAA Database Migrations

AQAA uses **Alembic** (configured in `backend/alembic/`) to version the
PostgreSQL schema. The async SQLAlchemy models in `backend/app/models/`
(registered via `backend/app/models/__init__.py`) are the single source of
truth -- Alembic's `--autogenerate` diffs the live database against
`Base.metadata` to produce migration scripts.

This directory does not contain migration scripts itself (those live in
`backend/alembic/versions/`); it documents the workflow for creating and
applying them against the local Docker datastores.

## 1. Start the local database

From the repository root:

```bash
docker compose up -d postgres
```

This starts PostgreSQL using the credentials in `.env` /
`backend/.env` (defaults: `aqaa` / `aqaa` / database `aqaa`, port `5432`).

Confirm it's healthy:

```bash
docker compose ps postgres
```

## 2. Configure the backend environment

```bash
cd backend
cp .env.example .env   # if you haven't already
```

Ensure `DATABASE_URL` in `backend/.env` points at the container:

```
DATABASE_URL=postgresql+asyncpg://aqaa:aqaa@localhost:5432/aqaa
```

Install dependencies (if not already):

```bash
pip install -r requirements.txt
```

## 3. Generate the initial migration

The repository currently has no migration scripts (`backend/alembic/versions/`
contains only `.gitkeep`). To generate the baseline migration covering every
model registered in `app/models/__init__.py` (Institution, Faculty,
Department, Programme, Module, User, File, FileVersion, DocumentRecord,
AuditRun, AuditFinding, and all enum types through Stage 14):

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
```

This connects to the database configured by `DATABASE_URL`, compares it
against `Base.metadata` (empty database -> full schema), and writes a new
file to `backend/alembic/versions/`.

**Always review the generated script before applying it** -- check enum
naming, nullable/FK definitions (especially the Stage 14 `audit_runs.module_id`
/ `audit_runs.programme_id` nullable + FK pair), and index/unique constraints
match the model definitions.

## 4. Apply migrations

```bash
alembic upgrade head
```

To check the currently applied revision:

```bash
alembic current
```

To see full history:

```bash
alembic history --verbose
```

## 5. Creating new migrations for future stages

Whenever a model changes (new table, new column, new enum value, etc.):

```bash
alembic revision --autogenerate -m "stage 15: <short description>"
alembic upgrade head
```

Commit the generated script in `backend/alembic/versions/` alongside the
model change in the same change set.

## 6. Rolling back

```bash
alembic downgrade -1     # one revision back
alembic downgrade base   # drop everything Alembic manages
```

## 7. Resetting the local database from scratch

```bash
docker compose down -v   # removes the aqaa_postgres_data volume
docker compose up -d postgres
cd backend
alembic upgrade head
python ../database/seed_data/run_all.py
```

## Notes

- `backend/alembic/env.py` injects `DATABASE_URL` from `app.config.settings`
  at runtime, so `alembic.ini`'s `sqlalchemy.url` placeholder never needs to
  be edited.
- Migrations run against the **async** engine via `AsyncConnection.run_sync`,
  matching the runtime database driver (`postgresql+asyncpg`).
- `database/schema.sql` is reserved for an exported, human-readable snapshot
  of the schema (e.g. via `pg_dump --schema-only`) for documentation/review
  purposes -- it is not used to provision the database. Alembic migrations
  are the source of truth.
