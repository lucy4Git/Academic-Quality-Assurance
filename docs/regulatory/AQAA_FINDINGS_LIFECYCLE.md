# AQAA Regulatory Findings Lifecycle

**Phase C | Version 1.0 | 2026-07-14**

---

## Overview

Regulatory findings are promoted from framework assessment gaps. They share the same 12-status finding lifecycle as audit findings (Stage B), extended with regulatory FK columns.

---

## 12-Status Lifecycle (Canonical)

```
OPEN → ACKNOWLEDGED → ASSIGNED → IN_PROGRESS → RESOLUTION_SUBMITTED
  → UNDER_REVIEW → RESOLVED
                 ↘ REJECTED → (back to OPEN or IN_PROGRESS)
OPEN ← REOPENED ← (from RESOLVED or REJECTED)
OPEN → ESCALATED
OPEN → DEFERRED → (returns to OPEN or CLOSED)
→ CLOSED
```

This lifecycle is defined in Stage B and must not be modified for Phase C.

---

## Regulatory-Specific Columns

Regulatory findings add FK columns not present in standard audit findings:

| Column | Type | Notes |
|--------|------|-------|
| `framework_version_id` | UUID FK nullable | Framework version the gap was found against |
| `criterion_id` | UUID FK nullable | Specific criterion that was unmet |
| `evidence_requirement_id` | UUID FK nullable | Specific evidence requirement not satisfied |
| `criterion_assessment_result_id` | UUID FK nullable | Link to the result row that sourced this finding |

---

## Gap Promotion

`POST /api/v1/framework-assessments/{run_id}/promote-gaps`

The service iterates unmet criteria from an assessment and creates findings, deduplicating on:
`(audit_run_id, framework_version_id, criterion_id)`

If a finding already exists for this combination, the existing finding is linked to the new result row rather than creating a duplicate.

---

## Severity Mapping

Criterion findings are assigned severity based on `is_mandatory`:

| Criterion type | Severity |
|----------------|---------|
| Mandatory criterion not met | `critical` |
| Non-mandatory criterion not met | `major` (default) |
| Evidence gap only | `minor` |

---

## Finding Resolution

When a regulatory finding reaches `RESOLVED`:

1. QA Officer verifies the evidence mapping that addressed the criterion
2. The evidence mapping transitions to `VERIFIED`
3. A re-assessment is recommended to update the compliance scores
4. The finding moves to `CLOSED` after the re-assessment confirms compliance

**Do not** close a finding without verifying the underlying evidence.

---

## Cross-Reference to Audit Findings

Regulatory findings are stored in the same `audit_findings` table as standard findings. They are distinguished by having `framework_version_id` or `criterion_id` populated.

The findings API returns both types and the frontend filters by the presence of these FK columns to display regulatory context.
