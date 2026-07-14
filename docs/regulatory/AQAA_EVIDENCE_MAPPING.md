# AQAA Regulatory Engine — Evidence Mapping

**Phase C | Version 1.0 | 2026-07-14**

---

## Purpose

Evidence mapping connects uploaded files (`file_uploads` table) to framework criteria (`framework_criteria`). The mapping state determines whether evidence counts toward a criterion's assessment score.

---

## Mapping States

| `validation_status` | Meaning | Counts in scoring? |
|--------------------|---------|-------------------|
| `pending` | Mapping created, not yet reviewed | No |
| `VERIFIED` | Approved by a QA Officer or above | Yes |
| `REJECTED` | Rejected — evidence insufficient or irrelevant | No |

Only VERIFIED mappings are used in `evidence_coverage_score` calculation.

---

## Creating a Mapping

```
POST /api/v1/framework-assessments/{run_id}/evidence-mappings

{
  "framework_version_id": "uuid",
  "criterion_id": "uuid",
  "file_id": "uuid",
  "mapping_source": "manual",
  "mapping_notes": "This assessment plan satisfies criterion CHE-IQA-S2-C1"
}
```

The service deduplicates on `(institution_id, file_id, criterion_id)` — submitting the same file→criterion link twice returns the existing mapping.

---

## Verifying a Mapping

```
PUT /api/v1/framework-assessments/evidence-mappings/{id}/verify

{ "approved": true, "validation_note": "Confirmed: document meets requirement" }
```

`approved: false` moves the mapping to REJECTED with an optional explanation.

**RBAC:** QA Officer and above.

---

## Automatic Mapping (Planned)

The evidence verification agent can propose mappings based on document content analysis. These are always created with `mapping_source = "ai_proposed"` and `validation_status = "pending"` — human verification is required before they affect scores.

**Do not** auto-approve AI-proposed mappings without human review.

---

## Evidence Requirements

Each criterion has `evidence_requirements[]` specifying:
- `evidence_type`: what kind of evidence is needed
- `minimum_count`: how many evidence items must be mapped and VERIFIED
- `maximum_age_days`: evidence freshness constraint
- `requires_signature`, `requires_approval`, `requires_date`, `requires_version`: document quality flags

The assessment engine checks these constraints when calculating `evidence_coverage_score`.
