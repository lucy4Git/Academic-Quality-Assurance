# AQAA Phase E — Formal Owner Approval

**Project:** Academic Quality Assurance Agent (AQAA)  
**Phase:** Phase E — Autonomous Quality Intelligence, Institutional Deployment and Continuous Improvement  
**Approval type:** Planning package closure and Sprint E0 commencement  
**Approval date:** 2026-07-17  
**Branch:** `feature/phase-e`  
**Baseline commit (at time of approval):** `af7b2af8eaf1c12e21b0dec8e2120e0ca6108e25`  
**Phase D tag:** `v0.9.0-phase-d` → `40b25ddfbb737322627ad33a48a4f212ef37e36f` (preserved; not modified by this approval)

---

## Scope of This Approval

This document records the formal owner approval of the AQAA Phase E planning package as prepared by AQAA Engineering and reviewed by an independent architecture, assurance, governance, research-methodology, and commercial assessor.

**This approval covers:**
- Phase E planning documentation closure
- Authorization of Sprint E0 commencement
- Acceptance of the planning package as the working basis for Phase E implementation (subject to conditions)
- Recorded owner decisions on workstreams, ADR status, governance boundaries, and pilot conditions

**This approval does NOT constitute:**
- Acceptance of every proposed ADR (all remain PROPOSED until individually confirmed during implementation)
- Institutional pilot approval
- Ethics committee approval
- Legal certification or regulatory clearance
- Authorization to process real institutional, staff, or student data
- Commitment that a specific institution has agreed to participate in the pilot

---

## Approval Statement

> "This approval authorizes Phase E planning closure and Sprint E0 commencement. It does not constitute institutional pilot approval, ethics approval, legal certification, acceptance of every proposed ADR, or authorization to process real institutional or personal data."

---

## Review Verdict

| Item | Result |
|------|--------|
| Independent review verdict | READY FOR OWNER APPROVAL WITH CONDITIONS |
| Owner decision | APPROVED_WITH_CONDITIONS |
| Review document | [AQAA_PHASE_E_OWNER_REVIEW_REPORT.md](AQAA_PHASE_E_OWNER_REVIEW_REPORT.md) |
| Discrepancies found and corrected | 4 (DISC-01 through DISC-04) — all RESOLVED before commit |

---

## Binding Conditions

### Condition OD-01 — Information Officer and Data-Processing Governance

Before Sprint E5 commences, before real institutional data is used, and before any external pilot deployment:

1. The Information Officer arrangement for the pilot must be confirmed in writing (per POPIA section 55)
2. A data-processing agreement must be in place between AQAA Engineering and the pilot institution
3. Privacy responsibilities must be clearly allocated between AQAA Engineering (as processor) and the pilot institution (as responsible party)
4. Institutional authorisation for the pilot must be obtained from an appropriate authority within the pilot institution

**Until these conditions are met:** Only synthetic, public, anonymised, or expressly pre-approved test data may be used. Real student, staff, or institutional records must not enter any AQAA environment.

### Condition OD-02 — Pilot Institution Engagement

Before Sprint E4 commences (week 9 of implementation):

1. The intended prospective pilot institution must be confirmed
2. Current engagement status must be communicated to the team in writing

**Language requirement:** Until a pilot institution has provided documentary confirmation of participation, all documentation and communications must use neutral wording: "prospective pilot institution" or "pilot institution to be confirmed." No institution may be described as an approved or confirmed pilot participant without documentary evidence.

---

## Owner Decisions

### Decision 1 — Phase E Title

**Approved:** Phase E — Autonomous Quality Intelligence, Institutional Deployment and Continuous Improvement

### Decision 2 — Approved Workstreams

The following seven workstreams are approved as the Phase E working framework:

| Workstream | Description |
|------------|-------------|
| E1 | Production-readiness foundation |
| E2 | Autonomous quality monitoring |
| E3 | Workflow and remediation automation |
| E4 | Institutional analytics and executive intelligence |
| E5 | Regulatory knowledge governance |
| E6 | Pilot deployment and onboarding |
| E7 | Evaluation and continuous improvement |

Sprint E0 (weeks 1–2) delivers the infrastructure foundation required to begin Workstream E1. Sprint E0 is authorized.

### Decision 3 — Sprint Roadmap

Sprints E0 through E7 are approved as the working implementation roadmap. Approximate timeline: 18 weeks.

| Sprint | Status |
|--------|--------|
| E0 | AUTHORIZED — may begin after planning commit is pushed |
| E1 | NOT_STARTED — SUBJECT_TO_E0_COMPLETION |
| E2 | NOT_STARTED — SUBJECT_TO_E1_GATE |
| E3 | NOT_STARTED — SUBJECT_TO_E2_GATE |
| E4 | NOT_STARTED — SUBJECT_TO_E3_GATE; OD-02 must be resolved |
| E5 | NOT_STARTED — SUBJECT_TO_E4_GATE |
| E6 | NOT_STARTED — SUBJECT_TO_E5_GATE; OD-01 must be resolved |
| E7 | NOT_STARTED — SUBJECT_TO_E6_COMPLETION |

### Decision 4 — ADR Status

All proposed Architecture Decision Records (ADR-0009 through ADR-0016) remain in `Status: PROPOSED`. Owner approval of the planning package does not constitute acceptance of any individual ADR. Each ADR must be confirmed individually during the relevant implementation sprint.

| ADR | Title | Status |
|-----|-------|--------|
| ADR-0009 | Background Task Queue (ARQ) | PROPOSED |
| ADR-0010 | Secrets Management (Docker secrets) | PROPOSED |
| ADR-0011 | Observability (structlog + Prometheus + Sentry) | PROPOSED |
| ADR-0012 | PDF Generation (WeasyPrint) | PROPOSED |
| ADR-0013 | Pilot Tenant Isolation (is_demo) | PROPOSED |
| ADR-0014 | Regulatory Knowledge Governance | PROPOSED |
| ADR-0015 | Reverse Proxy (Caddy) | PROPOSED |
| ADR-0016 | Analytics Aggregation (pre-aggregated snapshots) | PROPOSED |

### Decision 5 — Autonomous Action Governance Boundaries

The following boundaries apply to all Phase E automated and AI-assisted functionality. These are binding constraints on implementation:

1. **AQAA may:** detect, recommend, notify, draft, route, schedule, and escalate according to configured policy
2. **AQAA may not:** independently make final accreditation, disciplinary, regulatory, personnel, or institutional compliance decisions
3. **Consequential decisions require:** authorised human review and explicit approval before any outcome is recorded or communicated externally
4. **All automated actions must be:** logged in the AI audit log, attributable to a system actor, and explainable on request
5. **Human override must remain available** for all automated workflows at all times
6. **AI outputs in accreditation context must be labelled** as AI-assisted and subject to human verification

These boundaries apply to every workstream and sprint, including automated scheduling (E2), corrective action workflow (E3), regulatory grounding (E5), and pilot monitoring (E6).

### Decision 6 — Tenant Isolation Requirements

Application-layer row filtering is approved as the pilot isolation strategy, subject to all of the following controls being in place before pilot commencement:

- `institution_id` enforcement on all multi-tenant queries
- Repository-level service-layer filtering controls
- Qdrant tenant filters on all vector queries
- Object-storage tenant path boundaries
- Negative cross-tenant tests (confirmed passing in Sprint E5 gate)
- Audit logging of all cross-tenant access attempts
- Future evaluation of database-level row security (PostgreSQL RLS) as a defence-in-depth layer in Phase F

---

## Approval Limitations

This approval is limited to:
- Documentation and planning materials in `docs/phase-e/` and `docs/architecture/decisions/`
- Phase E planning package as described in `00_AQAA_PHASE_E_INDEX.md`
- Authorization to begin Sprint E0 implementation

This approval does not extend to:
- Any source code implementation (approval of implementation is implicit in each sprint delivery)
- Any database schema change (each Alembic migration requires engineering review before execution)
- External deployment or publication of the software
- Processing of real personal or institutional data
- Engagement of external pilot institutions on behalf of any named party

---

## Change-Control Procedure

Any of the following require a documented owner decision before proceeding:

1. **Scope expansion**: Adding features, capabilities, or workstreams not described in this planning package
2. **Pilot institution change**: Changing or adding pilot institutions requires OD-02 update
3. **Data governance change**: Any change to what data may be processed or stored requires OD-01 update
4. **ADR reversal**: Reversing an accepted ADR requires a new ADR entry with SUPERSEDES reference
5. **Sprint timeline change**: Extensions greater than two weeks per sprint require owner notification
6. **Phase F commencement**: Requires a separate planning package and formal approval

Minor implementation choices within the scope of an approved workstream (library versions, route naming, test coverage approaches, code organisation) do not require owner approval.

---

## Deferred Decisions

The following items are intentionally deferred to Phase F and must not be implemented in Phase E:

| Item | Reason |
|------|--------|
| SSO/SAML authentication | Phase F — enterprise deployment |
| Kubernetes / container orchestration | Phase F — multi-tenant scale |
| ECSA/HPCSA/SACE regulatory bodies | Phase F — professional body scope |
| Commercial billing and subscription management | Phase F — commercial launch |
| Inter-institution benchmarking | Phase F — requires multi-institution data governance |
| Native mobile application | Phase F |
| MongoDB production wiring | Phase F |
| QCTO (unless CHE/DHET overlap requires it) | Phase F |
| PostgreSQL Row-Level Security (RLS) | Phase F (after pilot validates need) |

---

## Prohibition on Assumed Pilot Approval

No document, communication, demo script, or user interface in this repository may represent a specific institution as an approved, confirmed, or participating pilot institution unless:

1. Written confirmation has been received from that institution's authorised representative
2. A data-processing agreement is in place
3. The OD-01 information officer arrangement is confirmed
4. The owner has received and acknowledged the confirmation

Until all four conditions are met, all references must use: **"prospective pilot institution"** or **"pilot institution to be confirmed."**

---

## Planning Package Scope

The approved planning package consists of:

**Planning documents (15):**
- AQAA_PHASE_D_CAPABILITY_INVENTORY.md
- AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md
- AQAA_PHASE_E_VISION_AND_SCOPE.md
- AQAA_PHASE_E_REQUIREMENTS.md
- AQAA_PHASE_E_ARCHITECTURE_PLAN.md
- AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md
- AQAA_PHASE_E_DATA_REQUIREMENTS.md
- AQAA_PHASE_E_REGULATORY_KNOWLEDGE_PLAN.md
- AQAA_PHASE_E_ROLE_EXPERIENCE_PLAN.md
- AQAA_PHASE_E_EVALUATION_PLAN.md
- AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md
- AQAA_PHASE_E_RISK_REGISTER.md
- AQAA_PHASE_E_SPRINT_ROADMAP.md
- AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md
- 00_AQAA_PHASE_E_INDEX.md

**Proposed Architecture Decision Records (8):**
- ADR-0009 through ADR-0016

**Governance documents:**
- AQAA_PHASE_E_OWNER_REVIEW_REPORT.md (independent review)
- AQAA_PHASE_E_OWNER_APPROVAL.md (this document)
- AQAA_PHASE_E_TRACEABILITY_VALIDATION.md

---

*Approval recorded by: AQAA Engineering — Release and Planning-Governance Lead*  
*Date: 2026-07-17*  
*Branch: feature/phase-e*  
*Commit at time of approval: af7b2af8eaf1c12e21b0dec8e2120e0ca6108e25*
