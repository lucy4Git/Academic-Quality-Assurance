# AQAA Regulatory and Quality Framework Engine — Architecture

**Date**: 2026-07-14  
**Phase**: C  

---

## 1. Architectural Position

The Regulatory Engine is a new vertical layer that sits **above** the existing institutional hierarchy and **beside** the existing AI audit agents:

```
┌─────────────────────────────────────────────────────────────┐
│              AQAA Platform                                   │
├─────────────────────────────────────────────────────────────┤
│  AI Orchestration Layer (C10)                               │
│  Regulatory intent resolution + context injection           │
├──────────────────────────┬──────────────────────────────────┤
│  Regulatory Engine (C1–C7)│  Existing Audit Agents (A–B)   │
│  Authority → Framework   │  Module Folder Audit             │
│  → Version → Standard    │  Assessment Compliance           │
│  → Criterion → Evidence  │  Moderation Compliance           │
│  → Assessment → Finding  │  Attendance Compliance           │
│                          │  Evidence Verification           │
│                          │  Outcome Alignment               │
│                          │  Accreditation Readiness         │
│                          │  Programme Review                │
├──────────────────────────┴──────────────────────────────────┤
│  Institutional Hierarchy (existing, preserved)              │
│  Institution → Faculty → Department → Programme → Module    │
├─────────────────────────────────────────────────────────────┤
│  Findings Centre (Stage B, preserved + extended)            │
│  12-status lifecycle · state machine · audit trail          │
├─────────────────────────────────────────────────────────────┤
│  Data Layer: PostgreSQL · Qdrant · Redis                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Domain Object Hierarchy

```
RegulatoryAuthority           (C1)
    └── QualityFramework       (C2)
            └── FrameworkVersion (C2)
                    ├── Standard (C3)
                    │       └── Criterion (C3)
                    │               └── EvidenceRequirement (C3)
                    └── ApplicabilityRule (C4)
                            └── [resolves to] Institution/Programme/Module/Assessment

EvidenceMapping               (C5)
    ├── links EvidenceRequirement ↔ File/AuditRun evidence
    └── produces FrameworkAssessmentRun

FrameworkAssessmentRun        (C5)
    └── CriterionAssessmentResult (C5)
            └── Gap → RegulatoryFinding → AuditFinding (C7)

CrossFrameworkMapping         (C6)
    ├── maps Criterion ↔ Criterion
    └── produces IntegratedReadinessReport
```

---

## 3. Key Architectural Decisions

### 3.1 Declarative Applicability Rules (NOT code execution)
Rules are stored as structured JSON conditions (not Python eval). A safe rule evaluator compares entity attributes against rule conditions. No `exec()`, no `eval()`, no Jinja templates with untrusted data.

Rule condition schema:
```json
{
  "operator": "AND",
  "conditions": [
    {"field": "programme.qualification_type", "op": "eq", "value": "B.Eng"},
    {"field": "programme.nqf_level", "op": "in", "value": [7, 8]},
    {"field": "institution.country", "op": "eq", "value": "ZA"}
  ]
}
```

### 3.2 Framework Versioning with Effective Dates
Every assessment references a specific `FrameworkVersion`. The applicability engine selects the version with the most recent `effective_from` ≤ assessment date and `effective_to` either null or > assessment date.

### 3.3 Evidence Reuse Across Frameworks
The `EvidenceMapping` table is the join between an evidence item and an `EvidenceRequirement`. The same file can satisfy requirements in multiple frameworks via separate mapping rows. Cross-framework deduplication avoids double-penalising the absence of shared evidence.

### 3.4 Mandatory Failure Visibility
Framework assessment scores are calculated at three levels: `mandatory_compliance_score` (fails on ANY mandatory criterion gap), `evidence_coverage_score`, and `quality_score`. These are never averaged together before surfacing mandatory failures.

### 3.5 AuditFinding Extension (not replacement)
Phase C adds nullable FKs to `AuditFinding`:
- `regulatory_authority_id`
- `framework_version_id`
- `standard_id`
- `criterion_id`
- `evidence_requirement_id`
- `citation_reference`
- `regulatory_risk`

The 12-status state machine from Stage B is preserved unchanged.

### 3.6 Tenant Isolation
- Institution-specific frameworks: `institution_id` on `QualityFramework`
- External/shared frameworks: `institution_id = NULL`, `is_public = TRUE`
- All assessment runs: `institution_id` scoped
- API layer: `_assert_tenant()` on every endpoint

---

## 4. Module Structure (New)

```
backend/app/
├── models/
│   ├── regulatory_authority.py        (C1)
│   ├── quality_framework.py           (C2)
│   ├── framework_version.py           (C2)
│   ├── framework_standard.py          (C3)
│   ├── framework_criterion.py         (C3)
│   ├── evidence_requirement.py        (C3)
│   ├── applicability_rule.py          (C4)
│   ├── evidence_mapping.py            (C5)
│   ├── framework_assessment.py        (C5)
│   └── cross_framework_mapping.py     (C6)
├── services/
│   ├── regulatory_authority_service.py (C1)
│   ├── quality_framework_service.py    (C2)
│   ├── applicability_service.py        (C4)
│   ├── evidence_mapping_service.py     (C5)
│   ├── framework_assessment_service.py (C5)
│   ├── cross_framework_service.py      (C6)
│   └── regulatory_findings_service.py  (C7)
├── routes/
│   ├── regulatory_authorities.py       (C1+C2)
│   ├── quality_frameworks.py           (C2)
│   ├── framework_assessments.py        (C5+C6)
│   └── regulatory_readiness.py         (C9)
└── schemas/
    └── regulatory.py                   (all schemas)

frontend/src/app/(main)/
├── framework-management/               (C8)
│   └── page.tsx
└── regulatory-readiness/               (C9)
    └── page.tsx
```

---

## 5. API Prefix Convention

All Phase C routes under `/api/v1/`:
- `/regulatory-authorities`
- `/quality-frameworks`
- `/framework-assessments`
- `/regulatory-readiness`
