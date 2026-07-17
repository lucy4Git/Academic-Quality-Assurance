# AQAA Phase D — Migration Validation

**Date:** 2026-07-17

---

## Current State

```
cd backend && python -m alembic current
→ 7602e7b39d25 (head)
```

Database is at migration head. ✅

```
cd backend && python -m alembic heads
→ 7602e7b39d25 (head)
```

Single head — no branch splits. ✅

---

## Migration Chain (21 migrations)

| Order | Revision | Description | Applied |
|-------|---------|-------------|---------|
| 1 | `99c7b97c9a76` | Initial schema | ✅ |
| 2 | `bcb42a8b6462` | Add programme QA fields | ✅ |
| 3 | `6bcc7db53782` | Add module audit tables | ✅ |
| 4 | `a1afe7223e2a` | Add audit evidence table | ✅ |
| 5 | `146ff3d10cd9` | Add audit history table | ✅ |
| 6 | `2a7b17360d01` | Phase 5 workflow comments notifications | ✅ |
| 7 | `7c5db84357e3` | Add ADIP registry tables | ✅ |
| 8 | `b0df78d4b8ec` | Add knowledge review tables | ✅ |
| 9 | `a1b2c3d4e5f6` | Add institution is_active | ✅ |
| 10 | `c4d5e6f7a8b9` | Add AI chat tables | ✅ |
| 11 | `e6f7a8b9c0d1` | Add user registration fields | ✅ |
| 12 | `d5e6f7a8b9c0` | Add qualification tables | ✅ |
| 13 | `f7a8b9c0d1e2` | Add institution registry fields | ✅ |
| 14 | `b2c3d4e5f6a7` | Add institutional knowledge foundation | ✅ |
| 15 | `c3d4e5f6a7b8` | Add acquisition engine | ✅ |
| 16 | `d4e5f6a7b8c9` | Add extraction engine | ✅ |
| 17 | `39b2fec2e97f` | Add finding status and history table | ✅ |
| 18 | `7a8b9c0d1e2f` | Canonical finding status lifecycle | ✅ |
| 19 | `a1b2c3d4e5f7` | Phase C regulatory framework engine | ✅ |
| 20 | `51694630069f` | Add source_status to regulatory tables | ✅ |
| 21 | `7602e7b39d25` | Phase D artifacts, actions, session extensions | ✅ |

---

## Validation Checks

| Check | Result |
|-------|--------|
| Database at head | ✅ `7602e7b39d25 (head)` |
| No duplicate heads | ✅ Single head |
| No missing revisions | ✅ Linear chain from 99c7b97c9a76 |
| No orphan revisions | ✅ All revisions in chain |
| 58 tables present | ✅ Verified via `\dt` |
| Migration history complete | ✅ `alembic_version` table has correct entry |

---

## Upgrade Commands

```bash
# From clean database
cd backend
python -m alembic upgrade head

# From specific revision
python -m alembic upgrade 7602e7b39d25

# Check current
python -m alembic current

# View history
python -m alembic history --verbose
```

---

## Downgrade Procedure

```bash
# Roll back one migration
cd backend
python -m alembic downgrade -1

# Roll back to specific revision
python -m alembic downgrade 51694630069f

# Roll back to before Phase D (removes ai_artifacts, ai_actions, session/message extensions)
python -m alembic downgrade 51694630069f
```

**Warning:** Migrations 1 (`99c7b97c9a76`) and 18 (`7a8b9c0d1e2f`) are marked irreversible. Downgrading past these will lose data or require manual DDL intervention.

---

## Irreversible Migrations

| Revision | Reason |
|---------|--------|
| `99c7b97c9a76` | Initial schema — dropping all tables destroys all data |
| `7a8b9c0d1e2f` | PostgreSQL ENUM types cannot be removed if used by existing data |

---

## Status

**VALID — database at head, no duplicate or orphan revisions.**
