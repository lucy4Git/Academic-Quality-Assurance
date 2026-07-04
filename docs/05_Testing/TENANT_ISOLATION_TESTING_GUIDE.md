# Tenant Isolation Testing Guide

**Version:** 1.1.0  
**Date:** 2026-07-02  
**Test files:** `backend/tests/test_tenant_isolation.py`, `backend/tests/test_archive_filter.py`, `backend/tests/test_auth_pilot.py`

---

## Overview

AQAA is a multi-tenant platform. Every data row carries an `institution_id`
foreign key, and `assert_institution_access()` in `backend/app/dependencies.py`
enforces 403 on cross-tenant access. This guide explains the isolation model
and how to run and extend the test suite.

---

## Isolation Model

### Row-level isolation

All institutional data tables (`faculties`, `departments`, `programmes`,
`modules`, `files`, `audit_runs`, etc.) carry `institution_id`. Services
scope all queries to the requesting user's institution.

### `assert_institution_access()`

Located in `backend/app/dependencies.py`. Called by route handlers before
returning any institution-scoped resource.

```python
def assert_institution_access(user: User, institution_id: UUID) -> None:
    if user.role == UserRole.SYSTEM_ADMIN:
        return          # SYSTEM_ADMIN bypasses all tenant checks
    if user.institution_id != institution_id:
        raise DomainPermissionError("Access denied: cross-tenant access")
```

SYSTEM_ADMIN is the only role that can read data across institutions.
All other roles (QA officer through student) are strictly scoped.

---

## Running the Tests

```bash
cd backend
python -m pytest tests/test_tenant_isolation.py -v
# Expected: 59 passed
```

Run the archive filter and auth pilot suites:

```bash
python -m pytest tests/test_archive_filter.py -v   # 25 tests: archive filter SQL + stats
python -m pytest tests/test_auth_pilot.py -v       # 38 tests: pilot login + blocked demo users
```

Run the full suite to confirm no regressions:

```bash
python -m pytest -q
# Expected: 654 passed
```

---

## Test Classes

| Class | Tests | What it covers |
|-------|-------|----------------|
| `TestAssertInstitutionAccess` | 6 | Core isolation function: admin bypass, TUT→UP 403, UP→TUT 403, all roles |
| `TestInstitutionListScoping` | 4 | List endpoint returns only own-institution data |
| `TestFacultyListScoping` | 3 | Faculty list scoped to institution |
| `TestDemoInstitutionArchiveStatus` | 4 | GFU/RCT is_active=False; TUT/UP is_active=True |
| `TestCrossTenantDirectIdAccess` | 4 | Direct-ID access blocked cross-tenant |
| `TestKnowledgeReviewInstitutionScoping` | 6 | KRC batch list/get scoped; cross-tenant get raises 403 |
| `TestUpSeedIdempotency` | 4 | UP seed helper functions produce consistent output |
| `TestTutSeedIdempotency` | 4 | TUT seed helper functions produce consistent output |
| `TestRbacTenantCombinations` | 24 | Parametrized: 6 roles × 4 scenarios |

---

## RBAC × Tenant Matrix

The `TestRbacTenantCombinations` class tests every role against four scenarios:

| Scenario | Expected |
|----------|----------|
| Access own institution | Allowed |
| Access other institution | 403 |
| SYSTEM_ADMIN access any | Allowed |
| Unauthenticated access | 401 |

Roles tested: `SYSTEM_ADMIN`, `QUALITY_ASSURANCE_OFFICER`, `FACULTY_DEAN`,
`HEAD_OF_DEPARTMENT`, `PROGRAMME_COORDINATOR`, `LECTURER`.

---

## Adding New Isolation Tests

When adding a new data model or service that is institution-scoped:

1. Add a test in `TestCrossTenantDirectIdAccess` that verifies direct-ID
   access raises `DomainPermissionError` when `institution_id` mismatches.
2. Add a list-scoping test to verify the service only returns own-institution
   rows for non-admin users.
3. Add the new resource to the RBAC matrix in `TestRbacTenantCombinations`
   if the access pattern differs from the default.

---

## Known Constraints

- SYSTEM_ADMIN users must never be scoped — do not add institution_id
  filtering to system admin queries.
- Demo institutions (GFU, RCT) have `is_active=False` but their data still
  exists and is protected by the same isolation rules.
- `assert_institution_access()` raises `DomainPermissionError`, which
  `main.py` maps to HTTP 403.
