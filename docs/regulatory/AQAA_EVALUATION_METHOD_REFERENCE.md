# AQAA Regulatory Engine — Evaluation Method Reference

**Phase C | Version 1.0 | 2026-07-14**

---

## Overview

Each `FrameworkCriterion` has an `evaluation_method` that determines how the assessment engine checks compliance. The engine uses a safe declarative evaluator — no `eval()` or `exec()`.

---

## Evaluation Methods

### `document_presence`

**Pass condition:** At least `minimum_count` VERIFIED evidence mappings exist for this criterion.

```python
evidence_found >= required_count  # True = pass
```

This is the most common method. Used when compliance requires submitting a document (e.g. a QA policy, an assessment plan).

---

### `count_threshold`

**Pass condition:** `evidence_found >= criterion.threshold`

Used when a specific number of instances is required (e.g. "at least 3 supervised clinical placements documented").

---

### `date_check`

**Pass condition:** At least one VERIFIED evidence mapping exists where the associated file's `created_at` is within `maximum_age_days` of the assessment date.

Used for time-sensitive evidence (e.g. "annual report must be from within the last 12 months").

---

### `boolean_rule`

**Pass condition:** Evaluated against `validation_rule` using the `_SAFE_OPS` safe evaluator.

```python
_SAFE_OPS = {
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "not": lambda a: not a,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}
```

Rules are structured declarative expressions, not executable code.

---

### `score_threshold`

**Pass condition:** The calculated `quality_score` for this criterion is ≥ `threshold`.

Used for qualitative criteria where multiple pieces of evidence contribute to a quality score.

---

### `human_review`

**Pass condition:** A human reviewer has manually marked the criterion as met.

Used for subjective criteria that cannot be determined from document presence alone (e.g. "teaching quality observed during site visit"). These always set `requires_human_review = true` on the criterion.

---

## Safe Evaluator

The safe evaluator operates on a declarative rule string resolved through `_SAFE_OPS`:

```python
# Example rule: "gte evidence_count 3 and lte evidence_age_days 365"
# Is NOT executed — only parsed against _SAFE_OPS dict
```

**Never add `eval()`, `exec()`, or `__import__` to the evaluator.** If a rule cannot be expressed using `_SAFE_OPS`, add a new lambda to the dict and document it here.
