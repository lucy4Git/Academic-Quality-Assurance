# AQAA Phase C — Implementation Plan

**Date**: 2026-07-14  
**Sprint**: Phase C  

---

## Execution Order

### Stage C0 ✅ COMPLETE
- Repository audit, baseline confirmation, 3 planning documents

### Stage C1 — Regulatory Authority Model
1. Add enums to `enums.py`: `AuthorityType`, `AuthorityStatus`
2. Create `models/regulatory_authority.py`
3. Add to `models/__init__.py`

### Stage C2 — Framework + Framework Version Model
1. Add enums: `FrameworkType`, `FrameworkScope`, `VersionStatus`
2. Create `models/quality_framework.py`
3. Create `models/framework_version.py`

### Stage C3 — Standards, Criteria, Evidence Requirements
1. Add enums: `EvaluationMethod`, `EvidenceType`
2. Create `models/framework_standard.py`
3. Create `models/framework_criterion.py`
4. Create `models/evidence_requirement.py`

### Stage C4 — Applicability Engine
1. Add enums: `ApplicabilityTargetType`
2. Create `models/applicability_rule.py`
3. Create `services/applicability_service.py` — safe declarative rule evaluator

### Stage C5 — Evidence Mapping + Framework Assessment
1. Add enums: `MappingSource`, `MappingValidationStatus`, `AssessmentStatus`
2. Create `models/evidence_mapping.py`
3. Create `models/framework_assessment.py` — `FrameworkAssessmentRun` + `CriterionAssessmentResult`
4. Create `services/framework_assessment_service.py`

### Stage C6 — Cross-Framework Compliance
1. Add enums: `CrossFrameworkRelation`
2. Create `models/cross_framework_mapping.py`
3. Create `services/cross_framework_service.py`

### Stage C7 — Findings Integration
1. Add nullable FK columns to `audit_findings` table (migration)
2. Extend `AuditFinding` model
3. Create `services/regulatory_findings_service.py`

### Stage C8 — Migration
1. Single Alembic migration for all Phase C tables
2. Seed test fixture authorities and frameworks

### Stage C9 — APIs
1. Create `routes/regulatory_authorities.py`
2. Create `routes/quality_frameworks.py`
3. Create `routes/framework_assessments.py`
4. Create `schemas/regulatory.py`
5. Register in `main.py`

### Stage C10 — Framework Management Workspace (Frontend)
1. Create `frontend/src/app/(main)/framework-management/`
2. Authority list + create
3. Framework list + version management
4. Standards/criteria hierarchy view

### Stage C11 — Regulatory Readiness Workspace (Frontend)
1. Create `frontend/src/app/(main)/regulatory-readiness/`
2. Framework applicability dashboard
3. Readiness by framework
4. Gap view + promote to findings

### Stage C12 — AI Orchestration Integration
1. Extend `agent_router_service.py` with regulatory intents
2. Context injection: applicable frameworks per entity

### Stage C13 — Tests + Documentation

---

## Constraints

- Do NOT alter existing `AuditFinding` state machine
- Do NOT alter existing accreditation workspace until new regulatory readiness is complete
- Do NOT fabricate official regulatory content
- All seed data: clearly labelled `[TEST FIXTURE]`
- Every new model: inherits `Base, UUIDPrimaryKeyMixin, TimestampMixin`
- Every new route: `_assert_tenant()` on all scoped endpoints
- Every framework change: audit log entry
