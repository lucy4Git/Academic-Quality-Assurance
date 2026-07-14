# AQAA Phase C — Completion Summary

**Date:** 2026-07-14  
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## What Phase C Delivers

Phase C adds a complete **Regulatory Framework Engine** to AQAA — the infrastructure for managing, assessing, and tracking compliance with quality frameworks from CHE, SAQA, DHET, ECSA, HPCSA, SACE, and QCTO.

---

## Completed Stages

| Stage | Description | Status |
|-------|-------------|--------|
| C0 | Enums (`AuthorityType`, `AuthorityStatus`, `VersionStatus`, `MappingType`, `EvaluationMethod`) | ✅ |
| C1 | Models: `RegulatoryAuthority`, `QualityFramework`, `FrameworkVersion` | ✅ |
| C2 | Models: `FrameworkStandard`, `FrameworkCriterion`, `EvidenceRequirement` | ✅ |
| C3 | Models: `EvidenceCriterionMapping`, `FrameworkAssessmentRun`, `CriterionAssessmentResult`, `CrossFrameworkMapping`, `RegulatoryFinding` + migration | ✅ |
| C4 | Regulatory authority service + routes | ✅ |
| C5 | Quality framework service + routes (with `selectinload` for versions) | ✅ |
| C6 | Evidence mapping service + cross-framework mapping service | ✅ |
| C7 | Framework assessment service (3-score engine with mandatory collapse) | ✅ |
| C8 | Regulatory findings service (gap promotion + deduplication) | ✅ |
| C9 | Frontend: Framework Management + Regulatory Readiness workspaces | ✅ |
| C10 | AI Regulatory Orchestration: 19 new intents, context resolver, execution planner, citation system | ✅ |

---

## Key Numbers

| Metric | Value |
|--------|-------|
| New database tables | 12 |
| New backend services | 7 |
| New API routes registered | 18+ |
| New intents in AI router | 19 |
| Total intents (C10) | 31 |
| Seeded test authorities | 7 |
| Seeded test frameworks | 5 |
| Backend tests passing | 1149 |
| Pre-existing failures (unrelated) | 3 |

---

## Architecture Invariants

These must not be changed without formal review:

1. **Three scores stored separately**: `mandatory_compliance_score`, `evidence_coverage_score`, `quality_score`
2. **Mandatory collapse**: single mandatory criterion failure → `mandatory_compliance_score = 0`
3. **Tenant isolation**: all queries scoped by `institution_id` at the service layer
4. **EQUIVALENT requires `human_verified = true`**: before cross-framework deduplication
5. **No `eval()`/`exec()`**: safe declarative `_SAFE_OPS` dict only
6. **Chain-of-thought not exposed**: `_RegulatoryExecutionPlan` is never returned to callers
7. **Citation required**: every regulatory claim must cite framework, version, and standard
8. **`[TEST FIXTURE]` disclosure**: computed `is_test_fixture` field disclosed in all API responses

---

## Files Introduced in Phase C

### Backend
- `backend/app/models/regulatory_authority.py`
- `backend/app/models/quality_framework.py`
- `backend/app/models/framework_version.py`
- `backend/app/models/framework_standard.py`
- `backend/app/models/framework_criterion.py`
- `backend/app/models/evidence_requirement.py`
- `backend/app/models/evidence_criterion_mapping.py`
- `backend/app/models/framework_assessment_run.py`
- `backend/app/models/criterion_assessment_result.py`
- `backend/app/models/cross_framework_mapping.py`
- `backend/app/models/regulatory_finding.py`
- `backend/app/models/applicability_rule.py`
- `backend/app/services/quality_framework_service.py`
- `backend/app/services/framework_assessment_service.py`
- `backend/app/services/evidence_mapping_service.py`
- `backend/app/services/cross_framework_service.py`
- `backend/app/services/regulatory_findings_service.py`
- `backend/app/services/regulatory_orchestration_service.py`
- `backend/app/routes/regulatory_authorities.py`
- `backend/app/routes/quality_frameworks.py`
- `backend/app/routes/framework_assessments.py`
- `backend/app/schemas/regulatory.py`
- `backend/alembic/versions/a1b2c3d4e5f7_phase_c_regulatory_framework.py`

### Frontend
- `frontend/src/lib/api/regulatoryFramework.ts`
- `frontend/src/app/(main)/framework-management/FrameworkManagement.tsx`
- `frontend/src/app/(main)/framework-management/page.tsx`
- `frontend/src/app/(main)/regulatory-readiness/RegulatoryReadiness.tsx`
- `frontend/src/app/(main)/regulatory-readiness/page.tsx`

### Database
- `database/seed_data/seed_regulatory_framework.py`

### Documentation (this directory)
- 15+ markdown documents in `docs/regulatory/`
