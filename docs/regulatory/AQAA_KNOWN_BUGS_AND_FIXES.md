# AQAA Regulatory Engine — Known Bugs and Fixes

**Phase C | Version 1.0 | 2026-07-14**

These are bugs that were discovered and fixed during Phase C implementation. Do not revert these fixes.

---

## 1. Python 3.13 + FastAPI 204 Body Assertion

**Symptom:** `AssertionError: Status code 204 must not have a response body`

**Cause:** In Python 3.13, FastAPI 0.115+ raises an assertion error when a route decorator specifies `status_code=status.HTTP_204_NO_CONTENT` and the route returns any object (including `None`).

**Fix:** Remove `status_code=status.HTTP_204_NO_CONTENT` from the decorator and return `Response(status_code=204)` explicitly.

```python
# Wrong
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(id: uuid.UUID) -> None:
    await svc.delete(db, id)

# Correct
@router.delete("/{id}")
async def delete_item(id: uuid.UUID) -> Response:
    await svc.delete(db, id)
    return Response(status_code=204)
```

**Affected files:** 12 route files had this pattern. All fixed.

---

## 2. `framework.versions` Null/Undefined Error

**Symptom:** `TypeError: Cannot read properties of undefined (reading 'filter')` in `FrameworkManagement.tsx`

**Cause:** The list endpoint for frameworks was not eagerly loading versions, so `framework.versions` was `undefined` in the frontend.

**Fix (backend):** Added `selectinload(QualityFramework.versions)` to the `list_frameworks()` query.

**Fix (frontend):** Added `?? []` null-safety guard: `(framework.versions ?? []).filter(...)`.

---

## 3. asyncpg DSN Scheme Mismatch

**Symptom:** `invalid DSN: scheme is expected to be either "postgresql" or "postgres", got 'postgresql+asyncpg'`

**Cause:** The seed script uses `asyncpg.connect()` directly (not SQLAlchemy), which does not accept the `+asyncpg` dialect prefix.

**Fix:** Strip the prefix in the seed script:
```python
DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
```

---

## 4. SYSTEM_ADMIN Role Case Mismatch

**Symptom:** `invalid input value for enum user_role: "system_admin"` during seed

**Cause:** The enum stored in PostgreSQL uses uppercase (`SYSTEM_ADMIN`). The query used lowercase.

**Fix:**
```python
# Wrong
"SELECT id FROM users WHERE role = 'system_admin'"

# Correct
"SELECT id FROM users WHERE role::text = 'SYSTEM_ADMIN' LIMIT 1"
```

---

## 5. Double `Depends()` Wrapping

**Symptom:** `TypeError: Depends(...) is not a callable object` on FastAPI 0.136.3+

**Cause:** Role dependency objects (`QAOfficerRequired`, `AdminRequired`, etc.) are already `Depends(_check)` objects. Wrapping them in a second `Depends()` breaks FastAPI's dependency resolution.

**Fix:** Use role dependencies directly as default values, never wrapped:
```python
# Correct
async def my_route(_: User = AdminRequired):

# Wrong
async def my_route(_: User = Depends(AdminRequired)):
```

---

## 6. `run_status.value` Redundancy

**Symptom:** Potential `AttributeError` when calling `.value` on a plain string

**Cause:** `AuditRun.run_status` is stored as a plain `str` (not an enum instance) after DB retrieval. Calling `.value` on it raises `AttributeError`.

**Fix:** Use the field directly in string interpolation: `f"...'{run.run_status}'..."` — do not call `.value`.

---

## 7. `check_programme_accreditation` vs `accreditation` Intent Precedence

**Symptom:** Test `test_local_dev_provider_skips_llm` expected `accreditation` but got `check_programme_accreditation`

**Cause:** Phase C added more specific regulatory intents. "Check programme accreditation status" now correctly matches `check_programme_accreditation` (more specific) rather than the generic `accreditation` intent.

**Fix:** Updated the test assertion to expect `check_programme_accreditation`. This is the correct and expected behaviour.
