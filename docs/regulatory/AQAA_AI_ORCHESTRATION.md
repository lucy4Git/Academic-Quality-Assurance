# AQAA Regulatory Engine — AI Orchestration

**Phase C | Version 1.0 | 2026-07-14**

---

## Overview

The AI Regulatory Orchestration layer routes user prompts to appropriate regulatory handlers, resolves regulatory context, and returns structured responses with mandatory citations and honest generation mode labelling.

---

## Intent Model (31 total)

### Original 12 intents

`assessment`, `moderation`, `attendance`, `evidence`, `outcome`, `accreditation`, `programme`, `qualification`, `knowledge`, `reporting`, `workflow`, `qa_general`

### 19 Regulatory intents (Phase C)

| Intent | Description |
|--------|-------------|
| `identify_applicable_frameworks` | Which frameworks apply to a programme or institution |
| `explain_applicability` | Why a framework applies to a specific entity |
| `assess_framework_compliance` | Assess compliance against a named framework |
| `assess_integrated_readiness` | Holistic readiness across multiple frameworks |
| `explain_regulatory_requirement` | What a specific criterion or standard requires |
| `find_missing_regulatory_evidence` | Evidence gaps for framework criteria |
| `compare_frameworks` | Compare or contrast two or more frameworks |
| `explain_framework_overlap` | Shared criteria between frameworks |
| `explain_framework_conflict` | Conflicting requirements across frameworks |
| `generate_regulatory_report` | Generate a compliance or readiness report |
| `generate_evidence_pack` | Assemble an evidence submission pack |
| `create_corrective_action_plan` | Create a remediation plan for findings |
| `explain_regulatory_finding` | Explain a regulatory finding and how to respond |
| `check_framework_version` | Check which version of a framework is current |
| `check_qualification_alignment` | NQF/HEQSF alignment for a qualification |
| `check_programme_accreditation` | CHE/DHET programme accreditation status |
| `check_professional_accreditation` | ECSA/HPCSA/SACE professional accreditation |
| `check_institutional_audit_readiness` | CHE site visit or DHET inspection readiness |
| `check_occupational_qualification_compliance` | QCTO/SETA occupational qualification compliance |

---

## Routing Pipeline

```
User prompt
    │
    ▼
llm_router_service.llm_route_prompt()
    │
    ├─ If LLM available: POST to provider with _ROUTER_SYSTEM_PROMPT
    │   → Returns { intent, agents, confidence, routing_reason }
    │
    └─ If LOCAL_DEV or provider error: detect_intent() keyword fallback
        → Returns (intent_label, confidence_float)
    │
    ▼
regulatory_orchestration_service.orchestrate_regulatory_query()
    │
    ├─ resolve_regulatory_context() — tenant isolation, effective frameworks
    ├─ _build_execution_plan() — INTERNAL, never exposed to callers
    ├─ _build_citations() — framework + version + standard references
    └─ RegulatoryResponse — returned to API caller
```

---

## Generation Modes

| Mode | When used | Notes |
|------|-----------|-------|
| `DETERMINISTIC_TEMPLATE` | Structured DB data → direct answer | No LLM involvement |
| `HYBRID` | DB data + LLM narrative synthesis | LLM synthesises explanation from retrieved facts |
| `LLM` | Open-ended regulatory question with retrieved context | LLM generates with RAG |
| `MANUAL_REVIEW_REQUIRED` | Conflicting requirements, high-stakes decisions | System cannot provide reliable answer; escalation required |

Generation mode is always disclosed to the caller in the response.

---

## Citation Requirements

Every regulatory answer sourced from framework content must include citations. A citation contains:

- `framework_code`
- `framework_name`
- `version_number`
- `standard_code` (if applicable)
- `criterion_code` (if applicable)
- `source_url` (if the framework version has a source URL)
- `is_test_fixture` (bool — always disclosed for stubs)

**Do not omit citations** to make responses appear cleaner.

---

## Chain-of-Thought Privacy

The `_RegulatoryExecutionPlan` object (internal) contains the reasoning steps used to plan a regulatory response. It is:

- Never serialized into API responses
- Never logged at INFO level (only DEBUG)
- Never returned to frontend clients

This prevents exposure of internal regulatory reasoning that could be exploited or misrepresented.

---

## Honest Disclosure Rules

1. If a framework is a test fixture: disclose with `is_test_fixture = true` in citations and add a caveat
2. If generation mode is `MANUAL_REVIEW_REQUIRED`: include caveat directing user to QA Officer
3. If confidence < 0.75: note in `routing_reason` that the intent may not match
4. Never claim a regulatory standard is authoritative without verifying `is_test_fixture = false`
