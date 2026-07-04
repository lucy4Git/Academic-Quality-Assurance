# AI Assistant & Reporting — Testing Guide

## Test files

| File | Tests | Coverage |
|------|-------|----------|
| `backend/tests/test_ai_assistant.py` | 38 | Intent classification, context retrieval, ask response, suggested prompts, recommendations, tenant isolation |
| `backend/tests/test_reporting.py` | 28 | CSV/Excel/PDF export, dashboard report lines, tenant isolation, compliance formula |

---

## Running tests

```bash
cd backend

# New Sprint 4 tests only
python -m pytest tests/test_ai_assistant.py tests/test_reporting.py -q

# Full suite (808 tests)
python -m pytest -q
```

---

## AI Assistant test classes

### TestIntentClassification (6 tests)
Verifies keyword matching for all 5 intents. The question "What subject is taught in semester 2?" must return `module_query`. Avoid ambiguous questions that hit both `programme` and `module` keywords.

### TestRetrieveContext (5 tests)
- Active institutions (TUT, UP) allowed; inactive (GFU, RCT) return `[]`.
- Qdrant `ValueError` → `[]` (graceful degradation).
- Mocked via `patch("app.ai_assistant.assistant_service.search_knowledge")`.

### TestAsk (13 tests including tenant isolation)
- All 8 required fields present in `AskResponse`.
- Institution code uppercased (`tut` → `TUT`).
- No-context path: `sources=[]`, `confidence_score=0.0`.
- Dev mode notice present in answer.
- `context_limit=999` capped at 20.
- TUT isolation: `search_knowledge` called with `institution_code="TUT"`.
- UP isolation: `search_knowledge` called with `institution_code="UP"`.
- GFU, RCT: `retrieve_context` returns `[]` without calling Qdrant.

### TestSuggestedPrompts (5 tests)
- Lecturer prompts have `prompt` and `category` keys.
- QA prompts ≥ lecturer count.
- Admin prompts contain `"Multi-institution"` category.
- Institution code interpolated in prompt text.

### TestRecommendations (8 tests)
No mocking needed — pure rule-based function.
- `non_compliant` → `high` priority present.
- `at_risk` → `medium` priority present.
- `missing_evidence_types=["assessment_brief"]` → action mentions "assessment brief".
- Output sorted `high → medium → low`.
- Each rec has `priority`, `category`, `action`, `rationale`.
- No duplicate actions.

---

## Reporting test classes

### TestExportCsv (7 tests)
- Returns bytes starting with `b"\xef\xbb\xbf"` (UTF-8 BOM).
- Headers and row data present in decoded text.
- Empty rows: returns `b"No data"` notice.

### TestExportExcel (8 tests)
- Returns valid xlsx (parsed by openpyxl).
- Has `Metadata` sheet.
- Custom sheet name applied.
- Header row present; data row present.
- Empty rows: no crash.
- Metadata sheet contains "AQAA".

### TestExportPdfPlaceholder (4 tests)
- Returns bytes.
- Contains "Placeholder" or "placeholder".
- Contains title string.
- Contains report lines.

### TestBuildDashboardReportLines (5 tests)
- Returns non-empty list.
- Contains module count.
- Contains institution code.
- Indexed collections labelled "INDEXED"; unindexed labelled "NOT INDEXED".

### TestTenantIsolation (3 tests)
- Non-admin accessing own institution: allowed.
- Non-admin accessing other institution: `PermissionError`.
- Admin accessing any institution: allowed.

### TestComplianceSummary (3 tests)
- Empty institution list → zero response, rate=0.0.
- Formula: 7/10 * 100 = 70.0.
- Unaudited floor: max(0, ...) never negative.

---

## Common mocking patterns

```python
# Mock Qdrant search
with patch("app.ai_assistant.assistant_service.search_knowledge") as mock:
    mock.return_value = [{"title": "...", ...}]
    result = retrieve_context("question", "TUT")

# Mock retrieve_context for ask tests
with patch("app.ai_assistant.assistant_service.retrieve_context") as mock:
    mock.return_value = chunks
    result = ask("question", "TUT")

# Mock async DB for tenant isolation
db = AsyncMock()
db.get = AsyncMock(return_value=mock_institution)
db.execute = AsyncMock(return_value=MagicMock(scalar_one=MagicMock(return_value=0)))
```
