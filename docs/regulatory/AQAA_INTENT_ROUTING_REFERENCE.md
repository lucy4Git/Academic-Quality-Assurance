# AQAA AI Workspace — Intent Routing Reference

**Phase C | Version 1.0 | 2026-07-14**

---

## How Routing Works

1. User types a prompt in the AI Workspace
2. `llm_router_service.llm_route_prompt()` sends the prompt to the LLM with `_ROUTER_SYSTEM_PROMPT`
3. LLM returns `{ intent, agents, confidence, routing_reason }` as JSON
4. If LOCAL_DEV provider or LLM call fails, falls back to `detect_intent()` keyword matching
5. The `agent_mode` is looked up from `_INTENT_TO_MODE`
6. For regulatory intents (`agent_mode = "regulatory"`): `orchestrate_regulatory_query()` is called
7. Response includes `citations`, `generation_mode`, `requires_human_review`, `suggested_next_actions`

---

## All 31 Intents

### Core QA Intents (12)

| Intent | Mode | Keyword triggers |
|--------|------|-----------------|
| `assessment` | assessment | assessment, marks, rubric, grades, exam |
| `moderation` | moderation | moderat*, second marker, double mark |
| `attendance` | attendance | attendance, register, sign-in, absent |
| `evidence` | evidence | evidence, portfolio, artefact, document, verify |
| `outcome` | outcome_alignment | outcome, graduate attribute, curriculum, alignment |
| `accreditation` | accreditation_readiness | accreditation, saqa, heqsf, ecsa, nqf level |
| `programme` | programme_review | programme review, periodic review, self-evaluation |
| `qualification` | qualification | gpa, cgpa, grade point, qualification |
| `knowledge` | knowledge_search | policy, regulation, statute, knowledge base |
| `reporting` | reporting | report, analytics, dashboard, statistics |
| `workflow` | workflow | approval, workflow, submission, deadline |
| `qa_general` | general | (fallback — no pattern match) |

### Regulatory Intents (19, Phase C)

All 19 map to `agent_mode = "regulatory"`.

| Intent | Primary keywords |
|--------|----------------|
| `identify_applicable_frameworks` | which framework, applicable framework |
| `explain_applicability` | why is framework applicable, how does apply |
| `assess_framework_compliance` | framework compliance, assess framework, meet standard |
| `assess_integrated_readiness` | integrated readiness, multi-framework, holistic compliance |
| `explain_regulatory_requirement` | what does criterion require, explain requirement |
| `find_missing_regulatory_evidence` | missing evidence, gaps in evidence, which documents missing |
| `compare_frameworks` | compare frameworks, difference between frameworks |
| `explain_framework_overlap` | overlap between frameworks, shared criteria |
| `explain_framework_conflict` | conflicting requirements, incompatible frameworks |
| `generate_regulatory_report` | regulatory report, generate framework report |
| `generate_evidence_pack` | evidence pack, evidence bundle, assemble evidence |
| `create_corrective_action_plan` | corrective action, remediation plan, fix finding |
| `explain_regulatory_finding` | regulatory finding, what does finding mean |
| `check_framework_version` | framework version, current version, latest edition |
| `check_qualification_alignment` | qualification alignment, nqf alignment, heqsf alignment |
| `check_programme_accreditation` | programme accreditation, che accreditation |
| `check_professional_accreditation` | professional accreditation, ecsa accreditation, hpcsa |
| `check_institutional_audit_readiness` | institutional audit readiness, che site visit |
| `check_occupational_qualification_compliance` | qcto, seta, occupational qualification, learnership |

---

## Generation Mode by Intent

| Generation Mode | Intents |
|----------------|---------|
| `DETERMINISTIC_TEMPLATE` | identify_applicable_frameworks, assess_framework_compliance, assess_integrated_readiness, find_missing_regulatory_evidence, generate_evidence_pack, check_framework_version |
| `HYBRID` | explain_applicability, explain_regulatory_requirement, compare_frameworks, explain_framework_overlap, generate_regulatory_report, create_corrective_action_plan, explain_regulatory_finding, check_qualification_alignment, check_programme_accreditation, check_professional_accreditation, check_institutional_audit_readiness, check_occupational_qualification_compliance |
| `MANUAL_REVIEW_REQUIRED` | explain_framework_conflict |
| `LLM` | All non-regulatory intents |

---

## Confidence Scoring

| Confidence | Interpretation |
|------------|----------------|
| ≥ 0.75 | High — routed with confidence |
| 0.5–0.74 | Medium — routing noted in response as possibly imprecise |
| < 0.5 | Low (keyword fallback only) — user invited to select a different agent |

LLM-returned confidence values are bounded to [0.0, 1.0].
