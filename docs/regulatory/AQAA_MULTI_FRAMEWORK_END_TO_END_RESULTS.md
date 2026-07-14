# AQAA Multi-Framework Scenario — End-to-End Results

**Phase C Closure Gate | 2026-07-14**

---

## Overview

This document records the execution results for all four domain multi-framework
scenarios. Each scenario exercises cross-framework applicability resolution,
citation generation, and intent routing using the seeded TEST FIXTURE data.

---

## Test Environment

- Backend: FastAPI 0.115, Python 3.13
- DB: PostgreSQL 16 (aqaa-postgres Docker container)
- Provider: LOCAL_DEV (deterministic template mode — no LLM)
- Branch: `recovery/semantic-grounding-and-audit-centre`
- Migration head: `51694630069f`

---

## Scenario 1 — Engineering Domain

**Applicable frameworks:** CHE-HEQ-2023, DHET-SPF-2022, SAQA-NQF-2012, ECSA-E-2022

| Test | Prompt | Intent detected | Mode | Result |
|------|--------|----------------|------|--------|
| E1 | "Which frameworks apply to our BEng programme?" | `identify_applicable_frameworks` | DETERMINISTIC_TEMPLATE | ✅ 4 frameworks returned |
| E2 | "Are we meeting ECSA-E-2022 criterion ENG-STD-001-C01?" | `assess_framework_compliance` | DETERMINISTIC_TEMPLATE | ✅ Framework + version cited |
| E3 | "What is integrated readiness across CHE and ECSA?" | `assess_integrated_readiness` | DETERMINISTIC_TEMPLATE | ✅ Both frameworks in response |
| E4 | "What documents are missing for ECSA professional accreditation?" | `find_missing_regulatory_evidence` | DETERMINISTIC_TEMPLATE | ✅ Evidence requirements listed |
| E5 | "What is the current version of the ECSA framework?" | `check_framework_version` | DETERMINISTIC_TEMPLATE | ✅ Version 2022.1 returned |

**Citations generated:** 4 (one per applicable framework)
**TEST FIXTURE warnings:** Present (all fixtures seeded with `[TEST FIXTURE]` prefix)
**Cross-tenant leakage:** None (TUT institution filter applied)

---

## Scenario 2 — Health Sciences Domain

**Applicable frameworks:** CHE-HEQ-2023, DHET-SPF-2022, SAQA-NQF-2012, HPCSA-MED-2023

| Test | Prompt | Intent detected | Mode | Result |
|------|--------|----------------|------|--------|
| H1 | "Which frameworks apply to our MBChB programme?" | `identify_applicable_frameworks` | DETERMINISTIC_TEMPLATE | ✅ 4 frameworks returned |
| H2 | "How does HPCSA-MED-2023 apply to our health faculty?" | `explain_applicability` | HYBRID | ✅ HPCSA in effective_frameworks |
| H3 | "What is our professional accreditation status with HPCSA?" | `check_professional_accreditation` | HYBRID | ✅ HPCSA-MED-2023 cited |
| H4 | "Compare CHE and HPCSA requirements for clinical training" | `compare_frameworks` | HYBRID | ✅ Both frameworks in citations |

**Citations generated:** 4 (one per applicable framework)
**TEST FIXTURE warnings:** Present
**Human review required:** No

---

## Scenario 3 — Teacher Education Domain

**Applicable frameworks:** CHE-HEQ-2023, DHET-SPF-2022, SAQA-NQF-2012, SACE-PGCE-2022

| Test | Prompt | Intent detected | Mode | Result |
|------|--------|----------------|------|--------|
| T1 | "Which frameworks apply to our PGCE programme?" | `identify_applicable_frameworks` | DETERMINISTIC_TEMPLATE | ✅ 4 frameworks returned |
| T2 | "Is our teaching practice placement SACE-compliant?" | `check_professional_accreditation` | HYBRID | ✅ SACE-PGCE-2022 cited |
| T3 | "What SACE criteria are we missing for teacher qualification?" | `find_missing_regulatory_evidence` | DETERMINISTIC_TEMPLATE | ✅ Evidence requirements from SACE |
| T4 | "Generate a PGCE regulatory report" | `generate_regulatory_report` | HYBRID | ✅ All 4 frameworks in response |

**Citations generated:** 4
**TEST FIXTURE warnings:** Present
**Human review required:** No

---

## Scenario 4 — Occupational Qualifications Domain

**Applicable frameworks:** QCTO-OQF-2021, SAQA-NQF-2012, DHET-SPF-2022

| Test | Prompt | Intent detected | Mode | Result |
|------|--------|----------------|------|--------|
| O1 | "Which frameworks apply to our QCTO learnership?" | `identify_applicable_frameworks` | DETERMINISTIC_TEMPLATE | ✅ 3 frameworks returned |
| O2 | "Are we compliant with QCTO occupational qualification requirements?" | `check_occupational_qualification_compliance` | HYBRID | ✅ QCTO-OQF-2021 cited |
| O3 | "What is the QCTO framework version we are assessed against?" | `check_framework_version` | DETERMINISTIC_TEMPLATE | ✅ Version 2021.1 returned |

**Citations generated:** 3
**TEST FIXTURE warnings:** Present
**Human review required:** No

---

## Cross-Framework Behaviour Validation

| Scenario | Behaviour | Validated |
|----------|-----------|-----------|
| EQUIVALENT mapping requires human_verified | No EQUIVALENT mappings in current fixtures — correctly treated as independent | ✅ |
| CONFLICTS_WITH triggers MANUAL_REVIEW_REQUIRED | Intent `explain_framework_conflict` → MANUAL_REVIEW_REQUIRED + caveat | ✅ |
| No double-counting of overlapping evidence | Each standard counted once per framework | ✅ |
| Mandatory failures not hidden | `requires_human_review` flag surfaced in regulatory event | ✅ |
| TEST FIXTURE caveat injected server-side | caveat present in all responses with is_test_fixture=True citations | ✅ |

---

## Result Summary

| Scenario | Tests | Pass | Fail |
|----------|-------|------|------|
| Engineering | 5 | 5 | 0 |
| Health Sciences | 4 | 4 | 0 |
| Teacher Education | 4 | 4 | 0 |
| Occupational | 3 | 3 | 0 |
| **Total** | **16** | **16** | **0** |

All 16 multi-framework scenario tests pass with TEST FIXTURE data.

---

## Notes

1. All tests run with `AI_PROVIDER=local_dev` — no LLM calls. DETERMINISTIC_TEMPLATE
   and HYBRID both produce correct structured responses in this mode.
2. HYBRID intents in LOCAL_DEV produce template-based answers (not LLM-generated),
   but the citations, frameworks, and caveats are all correct.
3. Production deployment with a real LLM will upgrade HYBRID answers to include
   narrative synthesis, but citations and framework lists remain deterministic.
