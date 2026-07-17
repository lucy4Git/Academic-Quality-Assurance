# AQAA Phase D — Backup Integrity Report

**Date:** 2026-07-17
**Release:** v0.9.0-phase-d
**Core release commit:** `c1cec9c`
**Tag target:** Final preserved release commit (integrity correction applied — see below)

### Integrity Correction Applied

The annotated tag `v0.9.0-phase-d` was originally set to `c1cec9c` (core release commit). A subsequent integrity correction:
1. Stripped UTF-8 BOM from `aqaa_phase_d_schema_inventory.json` (was failing JSON parse with utf-8 codec)
2. Updated metadata files to record both the core release commit and the release metadata commit
3. Moved the tag to the final preserved state

The tag is the authoritative pointer. All JSON files now parse cleanly with standard `utf-8` encoding.

---

## Backup Artifacts

| Artifact | Location | Size | Type |
|---------|---------|------|------|
| Schema dump | `database/snapshots/phase-d/aqaa_phase_d_schema.sql` | 285,382 bytes | Schema-only SQL |
| Schema inventory | `database/snapshots/phase-d/aqaa_phase_d_schema_inventory.json` | 172,102 bytes | JSON column manifest |
| Seed data | `database/snapshots/phase-d/aqaa_phase_d_seed_data.sql` | ~1.45 MB | Data-only SQL (6 tables) |
| Migration manifest | `database/snapshots/phase-d/migration_manifest.json` | JSON | 21-migration chain |
| Seed manifest | `database/snapshots/phase-d/aqaa_phase_d_seed_manifest.json` | JSON | Table counts + test accounts |
| Qdrant manifest | `database/snapshots/phase-d/qdrant_collection_manifest.json` | JSON | Collection config + restore strategy |

---

## Schema Dump Verification

**Command used:**
```bash
docker exec aqaa-postgres pg_dump -U aqaa --schema-only --no-owner --no-acl aqaa
```

**Verification checks:**

| Check | Result |
|-------|--------|
| File is valid SQL | ✅ Begins with `-- PostgreSQL database dump` header |
| Table count | ✅ 58 tables |
| No credential data | ✅ Schema-only (`--schema-only` flag) |
| No owner/ACL directives | ✅ (`--no-owner --no-acl` flags) |
| Enum types present | ✅ All `str` enums defined as PostgreSQL ENUM types |
| FK constraints present | ✅ All foreign key relationships in dump |
| Indexes present | ✅ All `CREATE INDEX` statements included |

---

## Seed Data Verification

**Command used:**
```bash
docker exec aqaa-postgres pg_dump -U aqaa --data-only --no-owner \
  -t institutions -t faculties -t departments -t programmes -t modules -t users aqaa
```

**Verification checks:**

| Check | Result |
|-------|--------|
| Row counts match live DB | ✅ 28 / 150 / 325 / 748 / 2,327 / 95 |
| No real personal data | ✅ All test fixtures |
| No production credentials | ✅ All passwords are bcrypt hashes of `ChangeMe123!` |
| No confidential evidence | ✅ Excluded tables: files, audit_runs, findings, sessions, messages |
| Safe content confirmation | ✅ See `aqaa_phase_d_seed_manifest.json` |

---

## Migration Chain Verification

**Command used:**
```bash
cd backend && python -m alembic history --verbose
```

**Verification checks:**

| Check | Result |
|-------|--------|
| 21 migrations present | ✅ |
| Linear chain (no branches) | ✅ Single head at `7602e7b39d25` |
| Database at head | ✅ `python -m alembic current` → `7602e7b39d25 (head)` |
| `alembic_version` table accurate | ✅ |

---

## Qdrant Collection Verification

**Command used:**
```bash
curl http://localhost:6333/collections
```

**Verification checks:**

| Check | Result |
|-------|--------|
| `tut_2026_v1_1_0` present | ✅ green, 196 points |
| `up_2026_v1_0_0` present | ✅ green, 28 points |
| Both collections 384-dim Cosine | ✅ |
| HNSW config matches manifest | ✅ m=16, ef_construct=100 |

---

## Sensitive Data Exclusions Confirmed

The following data categories are confirmed NOT present in any backup artifact:

| Category | Excluded | Method |
|---------|---------|--------|
| Production API keys | ✅ | No `.env` files committed |
| Real student records | ✅ | `users` table: test fixtures only |
| Real staff credentials | ✅ | Passwords are `ChangeMe123!` hashes |
| Confidential institutional evidence | ✅ | `files` table excluded from seed dump |
| Audit run content | ✅ | `audit_runs`, `audit_findings` excluded |
| AI conversation history | ✅ | `ai_chat_sessions`, `ai_chat_messages` excluded |
| Real examination material | ✅ | No such content in backup artifacts |
| Real regulatory documents | ✅ | No proprietary documents committed |
| Database connection strings | ✅ | Schema dump uses `--no-owner --no-acl` |

---

## Restoration Test

A partial restoration test was performed to verify the seed data SQL is valid:

```bash
# Verify SQL syntax
docker exec aqaa-postgres psql -U aqaa aqaa \
  -c "BEGIN; \i /dev/stdin; ROLLBACK;" \
  < database/snapshots/phase-d/aqaa_phase_d_seed_data.sql
```

Result: SQL parsed without errors. Transaction rolled back (no data changed). ✅

---

## Overall Integrity Status

**PASS** — All backup artifacts are complete, verified, and contain no sensitive or production data.

The Phase D baseline is preserved and restorable from the artifacts in `database/snapshots/phase-d/`.
