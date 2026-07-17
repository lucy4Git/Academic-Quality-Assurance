# AQAA Citation Validation Report

**Document:** AQAA_CITATION_VALIDATION_REPORT  
**Sprint:** Recovery Sprint — Stage A6 + A7  
**Date:** 2026-07-13  
**Status:** PASS — 0 invented citations across 10 queries

---

## Test Configuration

| Field | Value |
|-------|-------|
| Endpoint | `POST /api/v1/ai-assistant/ask` |
| Institution | TUT |
| User | TUT QA Officer (test account) |
| Embedding | FastEmbed BAAI/bge-small-en-v1.5, IS_PLACEHOLDER=False |
| Generation | deterministic_template (OpenAI quota exhausted, honest fallback) |
| Tool | PowerShell via `Invoke-RestMethod` |

---

## A6: Citation Inventory (10 queries)

| # | Query | Sources returned | Invented? | Note |
|---|-------|------------------|-----------|------|
| 1 | What programmes does TUT offer? | 5 IKP chunks (programme metadata) | No | All sources traceable to IKP |
| 2 | What are the modules in DPRS20? | 5 IKP chunks (DPRS20 module list) | No | Sources match retrieved module records |
| 3 | What is the NQF level for the Diploma in Computer Science? | 5 IKP chunks (DPRS20, NQF 6) | No | IKP payload confirms NQF 6 |
| 4 | How many credits is PPA115D? | 5 IKP chunks (module records) | No | Credit value from IKP record |
| 5 | What evidence is required for module folder compliance? | 5 IKP chunks (general) | No | No invented standards — answer stays within retrieved text |
| 6 | Which modules have 15 credits? | 5 IKP chunks (credit=15 matches) | No | Sources all have credit field matching |
| 7 | What is the module code for Computing Fundamentals? | 5 IKP chunks (CFA115D top result) | No | CFA115D confirmed in payload |
| 8 | What are the accreditation requirements for TUT? | 5 IKP chunks (programme/module metadata) | No | Answer stays in retrieved scope; no CHE/SAQA text invented |
| 9 | Tell me about the Bachelor of Technology in Computer Science | 5 IKP chunks (BTech programme) | No | Programme metadata present in IKP |
| 10 | What is COH115D about? | 5 IKP chunks (COH115D top result) | No | Module description from IKP payload |

**Invented citations: 0 / 10**

---

## A7: Generation Mode Labelling Verification

Checked `AskResponse` fields across the same 10 queries:

| Field | Expected | Observed |
|-------|----------|----------|
| `is_placeholder_mode` | `false` (embeddings are real) | `false` |
| `retrieval_mode` | `"semantic"` | `"semantic"` |
| `embedding_provider` | `"BAAI/bge-small-en-v1.5"` | `"BAAI/bge-small-en-v1.5"` |
| `generation_mode` | `"deterministic_template"` (OpenAI quota) | `"deterministic_template"` |
| `generation_provider` | `"none"` (fallback active) | `"none"` |
| `evidence_support_status` | `"chunks_retrieved"` | `"chunks_retrieved"` |

---

## is_placeholder_mode Bug Fix (A7)

**Before fix:** `is_placeholder_mode` was set to `True` inside the `except` block of `advanced_rag_service.advanced_ask()` whenever the LLM provider raised an exception (OpenAI `insufficient_quota`). This conflated two unrelated states — embedding quality and LLM generation fallback — into a single misleading boolean.

**After fix:** 
- `is_placeholder_mode` reads directly from `embedding_service.IS_PLACEHOLDER` (embedding state only)
- `generation_mode` / `generation_provider` / `evidence_support_status` are now separate fields tracking generation quality independently
- Same fix applied to `assistant_service.ask()` (secondary path)

**Files modified:**
- `backend/app/rag/advanced_rag_service.py` — primary path
- `backend/app/ai_assistant/assistant_service.py` — secondary path
- `backend/app/schemas/ai_assistant.py` — 5 new fields added to `AskResponse`

---

## Source Traceability

All 10 responses returned sources with populated `source_document` field pointing to IKP chunk origin (e.g. `ikp/institutions/TUT/2026/v1.0.0/ai/knowledge_chunks.json`). No response referenced a document not present in the retrieved `sources[]` array.

---

## Verdict

**Stage A6: PASS** — 0 invented citations across 10 grounded responses.  
**Stage A7: PASS** — Generation mode honestly labelled. `is_placeholder_mode` bug resolved. 5 new diagnostic fields present in all responses.
