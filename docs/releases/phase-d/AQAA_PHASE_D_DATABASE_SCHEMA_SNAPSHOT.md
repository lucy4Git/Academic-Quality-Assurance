# AQAA Phase D — Database Schema Snapshot

**Date:** 2026-07-17
**PostgreSQL Version:** 16.14 (Alpine)
**Database:** `aqaa`
**Migration Head:** `7602e7b39d25`

---

## Schema Dump

**File:** `database/snapshots/phase-d/aqaa_phase_d_schema.sql`
**Size:** 285,382 bytes
**Generated:** 2026-07-17

### Dump Command

```bash
docker exec aqaa-postgres pg_dump -U aqaa --schema-only --no-owner --no-acl aqaa \
  > database/snapshots/phase-d/aqaa_phase_d_schema.sql
```

### Contents

- All 58 table DDL statements (`CREATE TABLE`)
- All column definitions with types, constraints, defaults
- All indexes (`CREATE INDEX`)
- All unique constraints
- All foreign key constraints
- All enums (`CREATE TYPE`)
- All sequences
- Alembic version table
- No row data
- No passwords or connection strings

---

## Schema Inventory

**File:** `database/snapshots/phase-d/aqaa_phase_d_schema_inventory.json`
**Size:** ~172,102 bytes
**Format:** JSON array of column records

Each record contains:
- `table_name` — PostgreSQL table name
- `column_name` — column identifier
- `data_type` — PostgreSQL type
- `is_nullable` — YES/NO
- `column_default` — default expression or null
- `is_primary_key` — boolean
- `has_unique_constraint` — boolean

---

## Table Summary (58 tables)

| Table | Columns |
|-------|---------|
| `accreditation_bodies` | 10 |
| `accreditations` | 15 |
| `acquisition_jobs` | 13 |
| `acquisition_logs` | 12 |
| `acquisition_sources` | 15 |
| `adip_document_chunks` | 19 |
| `adip_documents` | 20 |
| `adip_extraction_candidates` | 19 |
| `adip_provenance_anchors` | 31 |
| `ai_actions` | 21 |
| `ai_artifacts` | 28 |
| `ai_chat_messages` | 21 |
| `ai_chat_sessions` | 20 |
| `alembic_version` | 1 |
| `applicability_rules` | 18 |
| `audit_checklist_items` | 9 |
| `audit_comments` | 9 |
| `audit_evidence` | 14 |
| `audit_findings` | 23 |
| `audit_history` | 8 |
| `audit_runs` | 18 |
| `campuses` | 15 |
| `contacts` | 16 |
| `criterion_assessment_results` | 23 |
| `cross_framework_mappings` | 17 |
| `departments` | 8 |
| `document_records` | 16 |
| `document_versions` | 9 |
| `downloaded_documents` | 23 |
| `evidence_mappings` | 17 |
| `evidence_requirements` | 21 |
| `extraction_candidates` | 22 |
| `extraction_runs` | 17 |
| `faculties` | 8 |
| `file_versions` | 10 |
| `files` | 17 |
| `finding_status_history` | 8 |
| `framework_assessment_runs` | 24 |
| `framework_criteria` | 19 |
| `framework_standards` | 15 |
| `framework_versions` | 19 |
| `graduate_attributes` | 12 |
| `institution_documents` | 14 |
| `institutions` | 16 |
| `knowledge_review_batches` | 19 |
| `knowledge_review_items` | 22 |
| `learning_outcomes` | 9 |
| `module_audits` | 25 |
| `modules` | 10 |
| `notifications` | 10 |
| `policies` | 13 |
| `policy_versions` | 11 |
| `programmes` | 13 |
| `qualifications` | 15 |
| `quality_frameworks` | 17 |
| `regulatory_authorities` | 20 |
| `schools` | 13 |
| `users` | 16 |

---

## Validation

### Command

```bash
# Create temporary test database and load schema
docker exec aqaa-postgres createdb -U aqaa aqaa_schema_test
docker exec -i aqaa-postgres psql -U aqaa aqaa_schema_test < database/snapshots/phase-d/aqaa_phase_d_schema.sql
docker exec aqaa-postgres psql -U aqaa aqaa_schema_test -c "\dt" | wc -l
docker exec aqaa-postgres dropdb -U aqaa aqaa_schema_test
```

### Expected Result

58 tables + header rows visible. Schema loads without errors.

### Validation Status

**VALID** — schema dump generated from live healthy database at migration head `7602e7b39d25`. All 21 migrations applied.

---

## Limitations

- No row data included (schema only)
- Extensions (e.g., `uuid-ossp`) must be installed before loading into a clean PostgreSQL instance
- `pgcrypto` or UUID extension required for default UUID generation
- Schema tested against PostgreSQL 16 — compatibility with earlier versions not verified
