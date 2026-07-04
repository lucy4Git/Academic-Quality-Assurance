# AI QA Assistant — Architecture Decision Record

**Status:** Implemented  
**Sprint:** 4  
**Subsystem:** `backend/app/ai_assistant/`

---

## Overview

The AI QA Assistant is a source-grounded question-answering subsystem that retrieves relevant context from the Qdrant vector store (IKP knowledge chunks) and assembles template-based answers.

It follows the **AI-First Hybrid Architecture (ADR-0005)**: AI returns findings and recommendations; humans make final compliance decisions.

---

## Design Constraints

| Constraint | Decision |
|-----------|----------|
| No external LLM available | Keyword-based intent classification + template assembly |
| No semantic embeddings in dev | Hash-based placeholder embeddings; all responses flagged `is_placeholder_mode=True` |
| Tenant isolation required | `institution_code` validated before every retrieval; GFU/RCT always excluded |
| Students must be blocked | All routes use `LecturerRequired` (blocks student role) |

---

## Component Map

```
routes/ai_assistant.py         ← HTTP layer, auth, institution_code resolution
  └─ assistant_service.py      ← classify_intent, retrieve_context, assemble_answer, ask
       └─ prompt_templates.py  ← DEV_MODE_NOTICE, ANSWER_WITH_CONTEXT, SUGGESTED_PROMPTS_*
       └─ knowledge_indexing/search_service.search_knowledge  ← Qdrant retrieval
  └─ recommendation_engine.py  ← rule-based get_recommendations (_RULES list)
schemas/ai_assistant.py        ← Pydantic request/response models
```

---

## Request Flow

```
POST /api/v1/ai-assistant/ask
  1. _resolve_institution_code()  — admin must supply code; non-admin resolved from DB
  2. classify_intent(question)    — keyword scoring → programme_query | module_query | compliance_query | audit_query | general
  3. retrieve_context()           — search_knowledge(question, institution_code, top_k)
                                  — returns [] for GFU/RCT or on any Qdrant error
  4. assemble_answer()            — preamble + ANSWER_WITH_CONTEXT or ANSWER_NO_CONTEXT + DEV_MODE_NOTICE
  5. return AskResponse           — question, answer, sources, confidence_score, is_placeholder_mode, suggested_followups
```

---

## Intent Classification

`classify_intent()` scores each intent by counting keyword hits (case-insensitive substring match). The intent with the highest score wins; ties go to the first intent in insertion order; zero matches returns `"general"`.

| Intent | Sample Keywords |
|--------|----------------|
| `programme_query` | programme, qualification, degree, btech, nqf |
| `module_query` | module, subject, credits, semester, lecturer |
| `compliance_query` | compliance, compliant, at risk, che, saqa |
| `audit_query` | audit, evidence, missing, finding |

---

## Tenant Isolation

- `ACTIVE_INSTITUTION_CODES = {"TUT", "UP"}` — defined in `search_service.py`
- `retrieve_context()` short-circuits to `[]` for any code not in this set
- Route handler validates the institution_code before calling the service
- Admin must explicitly supply `institution_code`; non-admin is locked to their own institution

---

## Recommendation Engine

`recommendation_engine.get_recommendations()` applies a `_RULES` list (10 rules). Each rule has:
- `trigger_status` — matches `audit_status`
- `trigger_missing` — matches items in `missing_evidence_types`
- `priority`, `category`, `action`, `rationale`

Rules fire when their trigger conditions match. Output is deduplicated and sorted `high → medium → low`.

---

## Dev Mode vs Production Mode

In dev mode (current):
- `embedding_service` uses hash-based vectors (not semantic)
- Every `AskResponse` has `is_placeholder_mode=True`
- `DEV_MODE_NOTICE` appended to every answer
- Frontend shows an amber warning banner

To activate production mode:
1. Configure a real sentence-transformers model in `EmbeddingService`
2. Re-index all collections
3. `is_placeholder_mode` will become `False` automatically (set by `embedding_service.is_placeholder`)

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/ai-assistant/ask` | Lecturer+ | Source-grounded Q&A |
| POST | `/ai-assistant/audit-summary` | Lecturer+ | AI summary of an audit run |
| POST | `/ai-assistant/recommendations` | Lecturer+ | Rule-based recommendations |
| GET | `/ai-assistant/suggested-prompts` | Lecturer+ | Role-aware prompt suggestions |
