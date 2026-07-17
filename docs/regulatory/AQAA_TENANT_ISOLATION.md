# AQAA Regulatory Engine — Tenant Isolation

**Phase C | Version 1.0 | 2026-07-14**

---

## Principle

Every database query in the regulatory engine must apply tenant filters. There are no admin bypasses. System Admins do not automatically receive access to all institution's regulatory data.

---

## Global vs Institution-Specific Records

| Record type | `institution_id` | Visible to |
|-------------|-----------------|-----------|
| Global authority | NULL | All institutions |
| Global framework | NULL | All institutions |
| Institution-specific framework | institution_id set | That institution only |
| Assessment runs | institution_id set | That institution only |
| Evidence mappings | institution_id set | That institution only |
| Regulatory findings | institution_id set | That institution only |

---

## Query Pattern

All service functions that list or fetch regulatory records must apply this filter:

```python
# Global + institution-specific
stmt = stmt.where(
    or_(
        QualityFramework.institution_id.is_(None),
        QualityFramework.institution_id == institution_id,
    )
)

# Global only (when institution_id is unknown)
stmt = stmt.where(QualityFramework.institution_id.is_(None))
```

**Do not** use `if is_admin: skip_filter` — this would be a tenant isolation bypass.

---

## Context Resolution

`regulatory_orchestration_service.resolve_regulatory_context()` resolves the caller's institution from the JWT-authenticated user object. The resolved `institution_id` is passed to all downstream queries.

If a user has no institution (e.g. a fresh System Admin with no assigned institution), only global frameworks are returned.

---

## Cross-Tenant Testing

When testing cross-tenant isolation:

1. Log in as a TUT user — should see global frameworks + TUT-specific frameworks only
2. Log in as a UP user — should see global frameworks + UP-specific frameworks only
3. A TUT user must NEVER see UP-specific frameworks, findings, or assessment results
4. System Admins see global frameworks but NOT other institutions' assessment data

---

## What NOT to Do

- **Do not** add a `bypass_tenant_filter=True` parameter to any service function
- **Do not** return all frameworks when role is SYSTEM_ADMIN
- **Do not** expose confidential evidence content to users outside the owning institution
- **Do not** add public Qdrant access that bypasses institution namespacing
- **Do not** log assessment results or evidence content unnecessarily
