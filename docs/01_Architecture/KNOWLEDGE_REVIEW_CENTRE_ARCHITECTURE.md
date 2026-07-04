# Knowledge Review Centre — Architecture

**Document ID:** ARCH-KRC-001  
**Version:** 1.0.0  
**Status:** Final  
**Last Updated:** 2026-07-01

---

## Overview

The Knowledge Review Centre (KRC) is the human-in-the-loop QA layer between the ADIP automatic extraction pipeline and the authoritative institutional knowledge base. QA officers review extracted field values, approve or reject them, and export a structured approved IKP package that feeds the AI knowledge base and the TUT database seed.

---

## Data Model

### KnowledgeReviewBatch

Groups all extracted candidates from a single ADIP run into a named, versioned unit of work.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| institution_id | UUID FK → institutions | Tenant boundary |
| batch_name | String(255) | Human-readable name |
| ikp_version | String(20) | e.g. `1.1.0` |
| academic_year | String(20) | e.g. `2026` |
| faculty_scope | String(100) | Optional faculty filter |
| status | String(30) | `ReviewBatchStatus` enum value |
| source_extraction_path | Text | Path to ADIP extracted/ dir |
| total_items | Integer | Counts updated after each item decision |
| approved_count | Integer | |
| rejected_count | Integer | |
| pending_count | Integer | |
| created_by | UUID FK → users | |
| reviewed_by | UUID FK → users | |
| closed_at | DateTime | |
| exported_at | DateTime | |
| export_path | Text | Path to approved/ dir after export |

### KnowledgeReviewItem

One field-level extracted value from a single candidate, awaiting a QA decision.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| batch_id | UUID FK → knowledge_review_batches | |
| institution_id | UUID FK → institutions | Tenant boundary (redundant copy for fast filtering) |
| candidate_id | String(255) | Original document_id from ADIP |
| entity_type | String(60) | `programme` / `module` / `admission_requirement` |
| entity_key | String(255) | Human-readable identifier (e.g. programme name) |
| field_name | String(100) | e.g. `nqf_level`, `total_credits` |
| extracted_value | Text | Raw or coerced value from ADIP |
| edited_value | Text | Reviewer correction (nullable) |
| confidence_score | Float | 0.0–1.0 |
| extraction_method | String(60) | ADIP extractor identifier |
| source_document | String(500) | ADIP document_id |
| page_number | Integer | Source PDF page |
| provenance_anchor_id | String(255) | Future: link to ADIPProvenanceAnchor |
| status | String(30) | `ReviewItemStatus` enum value |
| reviewer_id | UUID FK → users | |
| decision_reason | Text | |
| reviewed_at | DateTime | |
| academic_year | String(20) | |
| ikp_version | String(20) | |

---

## Enums

### ReviewItemStatus

| Value | Meaning |
|-------|---------|
| `pending_review` | Awaiting QA decision |
| `approved` | QA officer accepted extracted value |
| `rejected` | QA officer rejected item |
| `edited` | QA officer provided a corrected value |
| `quarantined` | Flagged for deeper investigation |
| `imported` | Successfully loaded into the DB |

### ReviewBatchStatus

| Value | Meaning |
|-------|---------|
| `open` | Items loaded, review not started |
| `in_review` | At least one item reviewed |
| `approved` | All items decided |
| `exported` | Approved IKP written to disk |
| `closed` | Archived / no further action |

---

## RBAC

| Operation | Required Role |
|-----------|--------------|
| List batches | QA Officer+ |
| Create batch | QA Officer+ |
| Create from ADIP | QA Officer+ |
| Get batch | Lecturer+ |
| List items | Lecturer+ |
| Get item | Lecturer+ |
| Approve item | QA Officer+ |
| Reject item | QA Officer+ |
| Edit item | QA Officer+ |
| Approve all eligible | QA Officer+ |
| Export approved IKP | QA Officer+ |

---

## Tenant Isolation

Every batch and item carries `institution_id`. Non-admin users can only see resources for their own institution (`assert_institution_access` called in every service function). `SYSTEM_ADMIN` bypasses this check.

---

## Confidence Thresholds

| Range | Badge Colour | Auto-approvable |
|-------|-------------|-----------------|
| ≥ 0.90 | Green | Yes (`approve_all_eligible`) |
| 0.70–0.89 | Yellow | No |
| < 0.70 | Red | No |

---

## Export Format

`POST /knowledge-review/batches/{id}/export-approved-ikp` writes to:

```
ikp/institutions/tut/{academic_year}/v{ikp_version}/approved/
  package.json               — metadata
  programmes.json            — list of programme objects
  modules.json               — list of module objects
  admission_requirements.json — list of admission requirement objects
  approval_summary.json      — statistics
```

Each entity object:
```json
{
  "entity_key": "Diploma In Computer Science",
  "fields": {
    "nqf_level": {
      "value": "6",
      "confidence": 0.92,
      "extraction_method": "nqf_credits_pattern",
      "source_document": "ea19be11-..."
    }
  },
  "approval_status": "approved",
  "reviewed_at": "2026-07-01T10:00:00+00:00"
}
```

---

## API

Base prefix: `/api/v1/knowledge-review`

| Method | Path | Description |
|--------|------|-------------|
| GET | /batches | List batches |
| POST | /batches | Create empty batch |
| POST | /batches/from-adip-output | Create + populate from ADIP JSON |
| GET | /batches/{id} | Get batch |
| POST | /batches/{id}/approve-all-eligible | Bulk auto-approve ≥ 0.90 |
| POST | /batches/{id}/export-approved-ikp | Export to approved/ dir |
| GET | /items | List items (?batch_id, ?entity_type, ?status) |
| GET | /items/{id} | Get item |
| POST | /items/{id}/approve | Approve |
| POST | /items/{id}/reject | Reject (reason required) |
| POST | /items/{id}/edit | Edit value |
