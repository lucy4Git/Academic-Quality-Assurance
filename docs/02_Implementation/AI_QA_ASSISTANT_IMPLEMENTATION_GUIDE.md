# AI QA Assistant — Implementation Guide

## Package structure

```
backend/app/ai_assistant/
├── __init__.py                 package docstring
├── assistant_service.py        classify_intent, retrieve_context, ask, get_suggested_prompts
├── prompt_templates.py         DEV_MODE_NOTICE, ANSWER_*, SUGGESTED_PROMPTS_*
└── recommendation_engine.py    get_recommendations(_RULES)

backend/app/schemas/ai_assistant.py   Pydantic models
backend/app/routes/ai_assistant.py    router at /ai-assistant

frontend/src/types/ai-assistant.ts    TypeScript interfaces
frontend/src/hooks/useAiAssistant.ts  TanStack Query hooks
frontend/src/app/(main)/ai-assistant/ page + AiAssistantView
```

---

## Key implementation notes

### institution_code resolution (route layer)

```python
async def _resolve_institution_code(db, current_user, requested_code) -> str:
    # Admin: must supply institution_code; validated against ACTIVE_INSTITUTION_CODES
    # Non-admin: institution_code resolved from DB (user.institution_id → Institution.code)
    # 422 if missing/invalid, 403 if cross-tenant attempt
```

### Dev mode flag

`is_placeholder_mode` comes from `embedding_service.is_placeholder`. It is `True` when hash-based embeddings are active. The frontend reads this from `AskResponse` and shows `<DevModeNotice />`.

### Adding new intent keywords

Edit `_INTENT_KEYWORDS` in `assistant_service.py`. Keep keywords as short substrings (e.g. `"diploma"` not `"diploma programme"`) so they match plurals and compound phrases.

### Adding new recommendation rules

Edit `_RULES` in `recommendation_engine.py`:

```python
{
    "trigger_status": "non_compliant",         # or None
    "trigger_missing": ["assessment_brief"],    # or []
    "priority": "high",
    "category": "Evidence",
    "action": "Upload assessment brief for all modules.",
    "rationale": "Assessment briefs are required for CHE compliance.",
}
```

Rules fire when EITHER trigger condition matches. Deduplication is by `action` string.

### Suggested prompts

`SUGGESTED_PROMPTS_STAFF`, `SUGGESTED_PROMPTS_QA`, `SUGGESTED_PROMPTS_ADMIN` in `prompt_templates.py` are lists of `{"prompt": ..., "category": ...}` dicts. The `{institution_code}` placeholder is interpolated by `get_suggested_prompts()`.

---

## Testing

```bash
cd backend
python -m pytest tests/test_ai_assistant.py -q
```

42 tests covering: intent classification, context retrieval, ask response structure, tenant isolation, recommended rules, suggested prompts, dev-mode flag.
