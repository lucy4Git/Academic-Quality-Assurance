# AQAA Regulatory Engine — Framework Applicability Engine

**Phase C | Version 1.0 | 2026-07-14**

---

## Purpose

The applicability engine determines which frameworks apply to a given entity (institution, programme, or module) at a given point in time.

---

## Resolution Logic

`regulatory_orchestration_service._resolve_effective_frameworks()`:

1. Query `quality_frameworks` where `is_active = true` AND (`institution_id IS NULL` OR `institution_id = :institution_id`)
2. For each framework, check that at least one version has `status = 'active'` AND is within effective date range
3. Return `(ids[], codes[])` for frameworks that pass both checks

---

## Applicability Rules

`framework_applicability_rules` stores structured rules that further refine which programmes or modules a framework applies to. Example rule types:

| Rule type | Example |
|-----------|---------|
| `programme_level` | Framework applies to NQF 7 programmes only |
| `faculty_scope` | Framework applies to Faculty of Engineering only |
| `qualification_type` | Framework applies to Bachelor of Engineering degrees only |
| `professional_body` | Framework applies when institution is ECSA-registered |

Applicability rules are evaluated at assessment trigger time. A framework that has rules but no matching rule for the target entity is excluded from the effective set.

---

## Effective Date Filtering

```python
(v.effective_from is None or v.effective_from <= today)
and (v.effective_to is None or v.effective_to >= today)
```

Frameworks where the active version's effective period does not include today are excluded even if `status = 'active'`. This handles:
- Future frameworks (not yet effective)
- Expired frameworks (superseded but not yet retired)

---

## Tenant Scope

The applicability engine always applies tenant isolation:

```python
# Global + institution-specific
where institution_id IS NULL OR institution_id = :institution_id
```

An institution cannot see another institution's custom frameworks.

---

## Use in AI Orchestration

When a user asks "which frameworks apply to my programme?", the orchestration service:

1. Calls `_resolve_effective_frameworks(institution_id=user.institution_id)`
2. Further filters by applicability rules for the target programme
3. Returns `effective_framework_codes` in the `RegulatoryContext`
4. The AI response cites the specific applicable frameworks with version numbers

The generation mode for `identify_applicable_frameworks` is `DETERMINISTIC_TEMPLATE` — the answer is fully derived from DB data without LLM involvement.
