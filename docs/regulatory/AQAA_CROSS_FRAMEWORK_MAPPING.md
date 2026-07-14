# AQAA Regulatory Engine — Cross-Framework Mapping

**Phase C | Version 1.0 | 2026-07-14**

---

## Purpose

Cross-framework mappings describe relationships between criteria or standards across different framework versions. They enable deduplication of evidence submission when multiple frameworks share equivalent requirements.

---

## Mapping Types

| Type | Meaning | Human verification required for use |
|------|---------|-------------------------------------|
| `EQUIVALENT` | Two criteria require identical evidence — evidence submitted for one satisfies the other | **Yes** — `human_verified = true` required |
| `OVERLAPPING` | Criteria are related but not identical — shared evidence may partially satisfy both | Recommended |
| `CONFLICTING` | Criteria have contradictory requirements | Yes — escalate to QA Officer |
| `SUPERSEDES` | One criterion replaces another in an updated standard | Yes |
| `RELATED` | Informational relationship only | No |

---

## Human Verification Requirement

**All cross-framework mappings are created with `human_verified = false`.**

EQUIVALENT mappings may only be used to deduplicate evidence after a qualified user has set `human_verified = true` via the verification endpoint.

```
PUT /api/v1/framework-assessments/cross-framework-mappings/{id}/verify
{ "human_verified": true }
```

**The system must never automatically treat two standards as legally equivalent without human verification.** This is a hard security constraint.

---

## Conflict Handling

When a CONFLICTING mapping exists between two frameworks that are both applicable to a programme:

1. The AI Workspace routes the query to `explain_framework_conflict` intent
2. Generation mode is set to `MANUAL_REVIEW_REQUIRED`
3. The response includes a caveat directing the user to their QA Officer
4. The conflict is not resolved automatically

**Do not** automatically choose one side of a conflict in AI-generated responses.

---

## Cross-Tenant Safety

Cross-framework mappings link framework **versions** — not institution-specific evidence. They are global (institution-agnostic). However, the evidence submitted against a mapped criterion remains institution-scoped.

A mapping between CHE-IQA and ECSA does not share evidence between TUT and UP — it only indicates that TUT's CHE evidence could satisfy ECSA criteria for TUT's own programmes.
