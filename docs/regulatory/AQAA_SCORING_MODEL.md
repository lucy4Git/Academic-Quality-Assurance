# AQAA Regulatory Engine — Compliance Scoring Model

**Phase C | Version 1.0 | 2026-07-14**

---

## Three-Score Architecture

The engine stores and returns three scores independently. They are never pre-merged before surfacing to the user.

| Score | Field | Calculation |
|-------|-------|------------|
| Mandatory Compliance | `mandatory_compliance_score` | 100 if ALL mandatory criteria met, **else 0** |
| Evidence Coverage | `evidence_coverage_score` | Verified evidence count / required count × 100, averaged across criteria |
| Quality | `quality_score` | Weighted average of non-mandatory criterion scores |
| Overall (derived) | `overall_score` | `mandatory × 0.4 + evidence × 0.4 + quality × 0.2` |

`overall_score` is computed on read and never stored.

---

## Mandatory Collapse Rule

**A single mandatory criterion failure collapses `mandatory_compliance_score` to 0.**

This is intentional. A programme that misses even one mandatory accreditation requirement is not compliant, regardless of how many non-mandatory criteria it satisfies.

```python
if any(not r.is_met for r in mandatory_results):
    mandatory_compliance_score = 0.0
else:
    mandatory_compliance_score = 100.0
```

This rule must not be changed to an average without a formal change review.

---

## Risk Level

| `mandatory_compliance_score` or `overall_score` | `risk_level` |
|-----------------------------------------------|-------------|
| ≥ 85 | `low` |
| ≥ 70 | `medium` |
| ≥ 50 | `high` |
| < 50 | `critical` |

Risk level is derived from `mandatory_compliance_score` first. If `mandatory_compliance_score = 0`, risk is `critical` regardless of other scores.

---

## Readiness Status

| Condition | `readiness_status` |
|-----------|-------------------|
| `mandatory_failures > 0` | `not_ready` |
| `mandatory_compliance_score ≥ 85` | `ready` |
| `mandatory_compliance_score ≥ 70` | `conditionally_ready` |
| Otherwise | `not_ready` |

---

## Evidence Coverage Calculation

```python
evidence_coverage = verified_mappings / required_evidence_count * 100
```

Only VERIFIED evidence mappings (`validation_status = 'VERIFIED'`) count. PENDING or REJECTED mappings do not contribute to coverage.

---

## What Scores Mean to Users

- **Mandatory = 0**: Programme has a blocking compliance failure. Accreditation cannot be recommended.
- **Evidence < 50**: Insufficient evidence uploaded or verified for meaningful assessment.
- **Quality < 70**: Non-mandatory quality indicators are not being met; improvement recommended.
- **Overall ≥ 85**: Generally ready for accreditation submission — confirm with your QA Officer.

---

## Immutability

These scoring rules are part of the core regulatory engine contract. Changes require:
1. Documented rationale
2. Review by QA Officer and Head of Department
3. Migration of historical assessment records
4. Re-training of any AI models that depend on score thresholds
