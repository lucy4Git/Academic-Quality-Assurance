# AQAA Regulatory Framework Engine — Data Model

**Phase C | Version 1.0 | 2026-07-14**

---

## Overview

The regulatory data model consists of 12 tables forming a hierarchy from authorities through frameworks, versions, standards, criteria, evidence requirements, and assessment results.

---

## Table Hierarchy

```
regulatory_authorities
  └── quality_frameworks
        └── framework_versions
              ├── framework_applicability_rules
              ├── framework_standards
              │     └── framework_criteria
              │           └── evidence_requirements
              ├── evidence_criterion_mappings
              └── framework_assessment_runs
                    ├── criterion_assessment_results
                    └── (→ regulatory_findings via promotion)

cross_framework_mappings (lateral — between framework_versions)
regulatory_findings (promoted from criterion_assessment_results)
```

---

## Table Definitions

### `regulatory_authorities`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| institution_id | UUID FK nullable | NULL = global authority |
| code | VARCHAR(40) UNIQUE | e.g. `CHE-ZA`, `ECSA-ZA` |
| name | VARCHAR(200) | Includes `[TEST FIXTURE]` prefix for stubs |
| short_name | VARCHAR(40) | Display abbreviation |
| authority_type | VARCHAR(40) | Enum: `quality_council`, `professional_council`, etc. |
| jurisdiction | VARCHAR(100) | e.g. `National` |
| country | VARCHAR(60) | ISO country code |
| is_external | BOOLEAN | |
| is_internal | BOOLEAN | |
| is_active | BOOLEAN | |
| status | VARCHAR(20) | `active`, `inactive`, `pending_review` |

### `quality_frameworks`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| authority_id | UUID FK → regulatory_authorities | |
| institution_id | UUID FK nullable | NULL = global framework |
| code | VARCHAR(40) UNIQUE | e.g. `CHE-IQA-2024` |
| name | VARCHAR(200) | |
| framework_type | VARCHAR(40) | `quality_assurance`, `accreditation`, etc. |
| scope | VARCHAR(40) | `institutional`, `programme`, `module` |
| jurisdiction | VARCHAR(100) | |
| is_mandatory | BOOLEAN | |
| is_public | BOOLEAN | |
| is_active | BOOLEAN | |

### `framework_versions`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| framework_id | UUID FK → quality_frameworks | |
| version_number | VARCHAR(20) | e.g. `2024.1` |
| version_label | VARCHAR(100) | Human-readable label |
| status | VARCHAR(20) | `draft`, `under_review`, `approved`, `active`, `superseded`, `retired`, `archived` |
| effective_from | DATE nullable | |
| effective_to | DATE nullable | |
| source_url | VARCHAR(500) nullable | Official source URL |
| approved_by_id | UUID FK nullable | User who approved |
| supersedes_version_id | UUID FK nullable | Previous version |

**Version lifecycle:** `DRAFT → UNDER_REVIEW → APPROVED → ACTIVE → SUPERSEDED | RETIRED → ARCHIVED`

Activating a version automatically SUPERSEDEs the previous ACTIVE version of the same framework.

### `framework_standards`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| framework_version_id | UUID FK | |
| parent_standard_id | UUID FK nullable | Self-referential for sub-standards |
| code | VARCHAR(30) | e.g. `CHE-IQA-S1` |
| title | VARCHAR(500) | |
| sequence | INTEGER | Display order |
| weight | FLOAT | Relative weight in scoring |
| is_mandatory | BOOLEAN | |
| citation_reference | TEXT nullable | |

### `framework_criteria`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| standard_id | UUID FK → framework_standards | |
| code | VARCHAR(40) | e.g. `CHE-IQA-S1-C1` |
| evaluation_method | VARCHAR(40) | `document_presence`, `count_threshold`, `date_check`, `boolean_rule`, `score_threshold`, `human_review` |
| is_mandatory | BOOLEAN | **Critical**: single mandatory failure collapses `mandatory_compliance_score` to 0 |
| requires_human_review | BOOLEAN | |
| threshold | FLOAT nullable | For count/score evaluations |
| weight | FLOAT | |

### `evidence_requirements`

Specifies what evidence a criterion needs to be satisfied.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| criterion_id | UUID FK | |
| evidence_type | VARCHAR(40) | `document`, `record`, `attestation`, `system_data`, `report` |
| code | VARCHAR(40) | |
| minimum_count | INTEGER | Default 1 |
| maximum_age_days | INTEGER nullable | Evidence freshness constraint |
| requires_signature | BOOLEAN | |
| requires_approval | BOOLEAN | |
| is_mandatory | BOOLEAN | |
| validation_rule | TEXT nullable | Safe declarative rule string (no eval/exec) |

### `evidence_criterion_mappings`

Links uploaded files to framework criteria with verification state.

| Column | Type | Notes |
|--------|------|-------|
| validation_status | VARCHAR(20) | `pending`, `VERIFIED`, `REJECTED` |
| validated_by_id | UUID FK nullable | Only VERIFIED mappings count in scoring |

### `framework_assessment_runs`

| Column | Type | Notes |
|--------|------|-------|
| mandatory_compliance_score | FLOAT nullable | 100 if ALL mandatory met, else 0 |
| evidence_coverage_score | FLOAT nullable | Verified evidence / required × 100 |
| quality_score | FLOAT nullable | Non-mandatory weighted average |
| overall_score | FLOAT nullable | mandatory×0.4 + evidence×0.4 + quality×0.2 |
| risk_level | VARCHAR(20) | `low` ≥85, `medium` ≥70, `high` ≥50, `critical` <50 |
| readiness_status | VARCHAR(30) | `ready`, `conditionally_ready`, `not_ready` |
| mandatory_failures | INTEGER | Count of mandatory criteria not met |

### `cross_framework_mappings`

| Column | Type | Notes |
|--------|------|-------|
| mapping_type | VARCHAR(20) | `EQUIVALENT`, `OVERLAPPING`, `CONFLICTING`, `SUPERSEDES`, `RELATED` |
| human_verified | BOOLEAN | Default FALSE — EQUIVALENT requires TRUE before deduplication use |
| verified_by_id | UUID FK nullable | |

---

## Tenant Isolation

- Global records: `institution_id = NULL`
- Institution-specific records: `institution_id` set to owning institution
- All queries MUST filter: `institution_id IS NULL OR institution_id = :institution_id`
- This is enforced at the service layer — routes must not bypass it

---

## Scoring Rules (Immutable)

1. `mandatory_compliance_score` = 100 if ALL mandatory criteria are met, else **0** — never averaged before surfacing
2. Single mandatory failure collapses the score to 0 regardless of total mandatory count
3. The three scores (`mandatory_compliance_score`, `evidence_coverage_score`, `quality_score`) are stored and returned separately
4. `overall_score` = `mandatory × 0.4 + evidence × 0.4 + quality × 0.2` — computed, never stored

These rules must not be modified without a formal change review.
