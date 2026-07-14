# AQAA Regulatory Engine — Framework Version Lifecycle

**Phase C | Version 1.0 | 2026-07-14**

---

## Version States

```
DRAFT
  ↓
UNDER_REVIEW
  ↓         ↙
APPROVED  ← (back to DRAFT for revision)
  ↓
ACTIVE ────────────────────┐
  ↓                        ↓
SUPERSEDED              RETIRED
  ↓                        ↓
ARCHIVED ←─────────────────┘
```

---

## Transition Rules

| From | Allowed targets |
|------|----------------|
| DRAFT | UNDER_REVIEW |
| UNDER_REVIEW | APPROVED, DRAFT |
| APPROVED | ACTIVE, DRAFT |
| ACTIVE | SUPERSEDED, RETIRED |
| SUPERSEDED | ARCHIVED |
| RETIRED | ARCHIVED |
| ARCHIVED | (none — terminal state) |

Transitions are enforced in `quality_framework_service.transition_version_status()`. Invalid transitions raise `DomainError` (HTTP 409).

---

## Auto-Supersede on Activation

When a version transitions to ACTIVE, the service automatically transitions any currently ACTIVE version of the **same framework** to SUPERSEDED.

This ensures only one version of a framework is active at any time.

```python
if new_status == VersionStatus.ACTIVE:
    # find existing ACTIVE versions of same framework and set to SUPERSEDED
    for prev in active_results:
        prev.status = VersionStatus.SUPERSEDED
```

---

## Assessment Version Pinning

`FrameworkAssessmentRun.framework_version_id` pins the assessment to the specific version that was current when the assessment ran. This ensures historical assessment results remain accurate even after the framework is updated.

- Do not change `framework_version_id` after an assessment is created
- Historical assessments against SUPERSEDED versions are still valid and should be preserved

---

## Effective Date Constraints

`effective_from` and `effective_to` on a version define the date range during which the version is operationally applicable. The applicability engine filters versions where:

```python
(effective_from IS NULL OR effective_from <= today)
AND (effective_to IS NULL OR effective_to >= today)
```

A version with `status = active` but past its `effective_to` date will not be returned by the framework resolver as an applicable framework.
