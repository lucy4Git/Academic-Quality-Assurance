# AQAA Regulatory Engine — Developer Guide

**Phase C | Version 1.0 | 2026-07-14**

---

## Adding a New Framework

### 1. Via Seed Script (test fixtures)

Add to `database/seed_data/seed_regulatory_framework.py`:

```python
AUTHORITIES.append({
    "code": "NEW-BODY-ZA",
    "name": "[TEST FIXTURE] New Regulatory Body",
    "short_name": "NRB",
    "authority_type": "professional_council",
    "jurisdiction": "National",
    "country": "ZA",
    "is_external": True,
    "is_internal": False,
    "is_active": True,
    "status": "active",
})

FRAMEWORKS.append({
    "authority_code": "NEW-BODY-ZA",
    "code": "NRB-STD-2024",
    "name": "[TEST FIXTURE] New Body Standards 2024",
    ...
    "versions": [...]
})
```

### 2. Via API (production)

```bash
# 1. Create authority
POST /api/v1/regulatory-authorities

# 2. Create framework
POST /api/v1/quality-frameworks

# 3. Create version (starts in DRAFT)
POST /api/v1/quality-frameworks/{fw_id}/versions

# 4. Create standards
POST /api/v1/quality-frameworks/versions/{ver_id}/standards

# 5. Add criteria via the quality framework service

# 6. Transition to ACTIVE
POST /api/v1/quality-frameworks/versions/{ver_id}/transition
{ "new_status": "active" }
```

---

## Adding a New Regulatory Intent

1. Add keyword patterns to `_INTENT_PATTERNS` in `agent_router_service.py`
2. Add to `_INTENT_TO_MODE` with mode `"regulatory"` (or a new mode if needed)
3. Add to `_NEXT_ACTIONS` (3 suggested actions)
4. Add to `_FOLLOW_UP_QUESTIONS` (2 follow-up questions)
5. Add to `intent_labels` in `_build_answer()`
6. Add to `source_map` in `_build_sources()`
7. Add to `AGENT_LABELS` in `llm_router_service.py`
8. Add to `_ROUTER_SYSTEM_PROMPT` in `llm_router_service.py`
9. Add generation mode mapping in `_build_execution_plan()` in `regulatory_orchestration_service.py`

---

## Adding a New Evaluation Method

1. Add the method name as a string constant
2. Add evaluation logic to `framework_assessment_service._evaluate_criterion()`
3. If rule-based: add new operator to `_SAFE_OPS` dict (lambda only — no `eval`/`exec`)
4. Update `AQAA_EVALUATION_METHOD_REFERENCE.md`
5. Add test cases in `tests/test_framework_assessment_service.py`

---

## Service Layer Conventions

- Services are pure async functions (no class state)
- All functions take `db: AsyncSession` as first argument
- Services raise domain exceptions (`NotFoundError`, `ConflictError`, `DomainError`, `DomainPermissionError`)
- Routes do NOT catch domain exceptions — let `main.py` exception handlers map them
- `actor: User` parameter carries the authenticated user for audit trail

---

## Import Patterns

```python
# Correct — import service functions directly
from app.services import quality_framework_service as svc

# Correct — use selectinload for eager loading
from sqlalchemy.orm import selectinload

stmt = select(QualityFramework).options(selectinload(QualityFramework.versions))
```

---

## Running Tests

```bash
cd backend

# Full suite (excludes broken knowledge indexing test)
python -m pytest -q --tb=short --ignore=tests/test_knowledge_indexing.py

# Specific test file
python -m pytest tests/test_agent_router.py -v

# Single test by name
python -m pytest -k "test_detect_intent" -v
```

---

## Common Mistakes to Avoid

1. **Double `Depends()`** — use `QAOfficerRequired` directly, never `Depends(QAOfficerRequired)`
2. **`status_code=204` in decorator** — return `Response(status_code=204)` instead
3. **Forgetting `selectinload`** — always load relationships you'll access in the service
4. **Calling `.value` on a plain string** — `run_status` from DB is already a string
5. **Forgetting `?? []` in frontend** — nullable arrays from API need null-safety guards
6. **Using `eval()`** — use `_SAFE_OPS` dict for rule evaluation
7. **Skipping fixture labelling** — always prefix test data with `[TEST FIXTURE]`
