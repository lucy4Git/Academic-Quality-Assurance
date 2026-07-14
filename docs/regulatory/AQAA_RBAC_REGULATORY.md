# AQAA Regulatory Engine — RBAC

**Phase C | Version 1.0 | 2026-07-14**

---

## Role Hierarchy (Cumulative)

```
SYSTEM_ADMIN
  → QUALITY_ASSURANCE_OFFICER
    → FACULTY_DEAN
      → HEAD_OF_DEPARTMENT
        → PROGRAMME_COORDINATOR
          → LECTURER
            → STUDENT
```

Higher roles inherit all permissions of lower roles.

---

## Regulatory Permissions

| Operation | Minimum Role |
|-----------|-------------|
| View regulatory authorities | QA Officer |
| View quality frameworks | QA Officer |
| View framework versions | QA Officer |
| View framework assessments | Programme Coordinator |
| Trigger framework assessment | Programme Coordinator |
| Upload evidence for framework | Programme Coordinator |
| Verify evidence mapping | QA Officer |
| Promote gaps to findings | QA Officer |
| View cross-framework mappings | QA Officer |
| Create cross-framework mapping | QA Officer |
| Verify cross-framework mapping | QA Officer |
| Create/update frameworks | System Admin |
| Create/update versions | System Admin |
| Transition version status | System Admin |
| Create/update authorities | System Admin |
| Deactivate authority | System Admin |

---

## FastAPI Dependency Usage

Role guards are defined in `backend/app/dependencies.py` as `Depends(_check)` objects:

```python
# Correct — use directly as default value
@router.get("", response_model=...)
async def list_frameworks(
    _: User = QAOfficerRequired,  # ✓
):
    ...

# Wrong — do NOT double-wrap
@router.get("")
async def list_frameworks(
    _: User = Depends(QAOfficerRequired),  # ✗ raises TypeError in FastAPI 0.136.3+
):
    ...
```

See CLAUDE.md "Known backend bugs fixed" for the double-`Depends()` constraint.

---

## Student Access

Students (role = STUDENT) have **no access** to regulatory framework data. Framework assessments, evidence mappings, and compliance scores are not exposed to students.

If a student attempts to access a regulatory endpoint, the server returns `403 Forbidden`.

---

## System Admin Scope

System Admins can create and manage the framework catalogue (authorities, frameworks, versions, standards, criteria). However:

- System Admins do NOT automatically see all institutions' assessment data
- Tenant isolation applies to System Admins when they are assigned to a specific institution
- A System Admin with no institution assignment sees global frameworks only
