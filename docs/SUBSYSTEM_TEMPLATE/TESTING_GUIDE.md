# [Subsystem Name] — Testing Guide

**Subsystem:** [Name]  
**Document Type:** Testing Guide  
**Version:** 1.0.0  
**Last Updated:** YYYY-MM-DD

---

## Test Strategy

| Test Type | Coverage Target | Tool |
|-----------|----------------|------|
| Unit tests | Service functions, helpers | pytest |
| Integration tests | API endpoints end-to-end | pytest + httpx |
| Frontend type checking | All TypeScript types | tsc --noEmit |
| Lint | Code style + rules | ESLint |
| Build | Production build validity | next build |

---

## Running Tests

```bash
# Full backend test suite
cd backend && python -m pytest -q

# Single test file
cd backend && python -m pytest tests/test_[file].py -q

# Single test by name
cd backend && python -m pytest -k "test_[name]" -q

# Frontend checks (run all three)
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

---

## Test Cases

### Backend Test Cases

| Test ID | Function Tested | Test File | Status |
|---------|----------------|-----------|--------|
| T-001 | `[function_name]()` | `tests/test_[file].py` | ✅ Passing |
| T-002 | [Next test] | | ⏳ Planned |

### Critical Test Scenarios

#### Scenario 1 — [Name]
**Given:** [Initial state]  
**When:** [Action taken]  
**Then:** [Expected result]

```python
# Example test structure
async def test_[scenario_name](db, client, auth_headers):
    # Given
    [setup]
    
    # When
    response = await client.post("/api/v1/[path]", json={...}, headers=auth_headers)
    
    # Then
    assert response.status_code == 201
    assert response.json()["field"] == expected_value
```

#### Scenario 2 — Tenant Isolation
**Given:** User from Institution A  
**When:** They attempt to access Institution B data  
**Then:** HTTP 403 Forbidden

---

## Test Data

[Describe what test data is needed and where to get it]

All tests should use the seeded demo data (GFU/RCT) available via `database/seed_data/run_all.py`.

Default test credentials: `ChangeMe123!` for all seeded users.

---

## Regression Tests

After modifying this subsystem, verify these existing tests still pass:

| Test | File | Covers |
|------|------|--------|
| [existing test] | `tests/test_[file].py` | [what it verifies] |

---

## Known Test Gaps

| Gap | Priority | Ticket |
|-----|----------|--------|
| [Missing coverage] | High/Medium/Low | [reference] |
