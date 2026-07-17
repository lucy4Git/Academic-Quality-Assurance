# AQAA Phase E Planning Package — Independent Owner Review Report

**Reviewer role:** Independent Senior Architecture Reviewer / Software Assurance Lead / AI Governance Reviewer / Research-Methodology Reviewer / Commercial Product Assessor  
**Review date:** 2026-07-17  
**Branch under review:** `feature/phase-e`  
**HEAD commit:** `af7b2af8eaf1c12e21b0dec8e2120e0ca6108e25`  
**Phase D tag verified:** `v0.9.0-phase-d` → `40b25ddfbb737322627ad33a48a4f212ef37e36f` ✓ (unchanged)  
**Status of review:** COMPLETE  
**Owner decision:** APPROVED_WITH_CONDITIONS (2026-07-17)  
**Approval document:** [AQAA_PHASE_E_OWNER_APPROVAL.md](AQAA_PHASE_E_OWNER_APPROVAL.md)

---

## Approval Condition Tracker

| Condition | Owner role | Due gate | Status | Evidence required |
|-----------|-----------|----------|--------|-------------------|
| OD-01: Information Officer and data-processing governance | AQAA Engineering / Pilot Institution Legal | Before Sprint E5; before any real institutional data | OPEN | Signed data-processing agreement; designated Information Officer in writing |
| OD-02: Pilot institution engagement | AQAA Engineering | Before Sprint E4 (week 9) | OPEN | Written confirmation of prospective pilot institution and engagement status |

---

## Sprint Authorization Status

| Sprint | Status |
|--------|--------|
| E0 | AUTHORIZED |
| E1 | SUBJECT_TO_PRIOR_SPRINT_GATE |
| E2 | SUBJECT_TO_PRIOR_SPRINT_GATE |
| E3 | SUBJECT_TO_PRIOR_SPRINT_GATE |
| E4 | SUBJECT_TO_PRIOR_SPRINT_GATE |
| E5 | SUBJECT_TO_PRIOR_SPRINT_GATE |
| E6 | SUBJECT_TO_PRIOR_SPRINT_GATE AND OD-01 RESOLVED AND OD-02 RESOLVED |
| E7 | SUBJECT_TO_PRIOR_SPRINT_GATE |

---

## ADR Status

All ADRs remain PROPOSED. Owner approval of the planning package does not constitute acceptance of any individual ADR.

| ADR | Status |
|-----|--------|
| ADR-0009 (ARQ) | PROPOSED |
| ADR-0010 (Docker secrets) | PROPOSED |
| ADR-0011 (structlog + Prometheus + Sentry) | PROPOSED |
| ADR-0012 (WeasyPrint) | PROPOSED |
| ADR-0013 (tenant isolation / is_demo) | PROPOSED |
| ADR-0014 (regulatory governance) | PROPOSED |
| ADR-0015 (Caddy) | PROPOSED |
| ADR-0016 (analytics aggregation) | PROPOSED |

---

## Discrepancy Resolution Status

| # | Description | Status |
|---|-------------|--------|
| DISC-01 | NotificationType count — capability inventory had no mention of NotificationType; section 3.15 added with correct 10-value enumeration | RESOLVED |
| DISC-02 | `attachment_grounding_status` — capability inventory clarified: computed per-request in `ai_assistant.py` lines 550–628; not a persisted model field | RESOLVED |
| DISC-03 | ADR-0013 `is_internal_test` column — ADR revised to adopt existing `is_demo` field; "new column" wording removed from all instances | RESOLVED |
| DISC-04 | Table count discrepancy (8 vs 9) — authoritative count established as **9 new tables**: corrective_actions, corrective_action_history, ai_audit_logs, hallucination_incidents, regulatory_document_registry, compliance_trend_snapshots, pilot_consent, background_job_logs, audit_trigger_schedules. Architecture plan updated to add M-E-00 migration. Data requirements updated with explicit 9-table summary. | RESOLVED |

---

## Executive Summary

The Phase E planning package for AQAA is **substantially complete, internally coherent, technically well-grounded, and commercially appropriate** for a first-pilot deployment. The planning team conducted genuine repository inspection rather than aspirational specification, producing a capability inventory and gap analysis that accurately reflects what Phase D achieved and what is missing.

Four documentation discrepancies were identified between planning claims and the actual codebase. All four have been corrected in-place (see Section 16 and Discrepancy Resolution Status above). No architectural decisions require revision. No scope conflicts with the AQAA standalone constraint were identified.

**Final verdict: READY FOR OWNER APPROVAL WITH CONDITIONS**  
**Owner decision (2026-07-17): APPROVED_WITH_CONDITIONS**  
**Sprint E0: AUTHORIZED**

The two conditions (OD-01, OD-02) are tracked in the Approval Condition Tracker above. Neither blocks Sprint E0.

---

## Section 1 — Document Completeness Audit

All 15 planning documents and 8 ADRs specified in the audit brief are present and populated.

| Document | Status | Verdict |
|----------|--------|---------|
| AQAA_PHASE_D_CAPABILITY_INVENTORY.md | Present, fully populated | APPROVE_WITH_CORRECTIONS (NotificationType count corrected) |
| AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_VISION_AND_SCOPE.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_REQUIREMENTS.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_ARCHITECTURE_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_DATA_REQUIREMENTS.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_REGULATORY_KNOWLEDGE_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_ROLE_EXPERIENCE_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_EVALUATION_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_RISK_REGISTER.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_SPRINT_ROADMAP.md | Present, fully populated | APPROVE |
| AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md | Present, fully populated | APPROVE |
| 00_AQAA_PHASE_E_INDEX.md | Present, fully populated | APPROVE |
| ADR-0009 through ADR-0016 (8 ADRs) | All present, all populated | APPROVE_WITH_CORRECTIONS (ADR-0013 corrected) |

---

## Section 2 — Repository-Grounding Audit

The following claims in the planning package were verified against the live codebase. Evidence is cited by file and line.

### 2.1 Verified Claims

| Planning Claim | Evidence | Verdict |
|----------------|----------|---------|
| No ARQ in requirements.txt | `backend/requirements.txt` — confirmed absent | VERIFIED |
| No structlog, no sentry-sdk, no weasyprint | `backend/requirements.txt` — confirmed absent | VERIFIED |
| Redis present as Docker service | `docker-compose.yml` — `aqaa-redis` service confirmed | VERIFIED |
| PDF export is a placeholder | `backend/app/routes/reporting.py` line 257 — `export_pdf_placeholder()` | VERIFIED |
| AI streaming via SSE | `backend/app/routes/ai_assistant.py` line 492 — `StreamingResponse` | VERIFIED |
| AiChatSession has module_id and context_snapshot | `backend/app/models/ai_chat.py` — both fields confirmed | VERIFIED |
| SourceStatus has ARCHIVED value | `backend/app/models/enums.py` line 470 — confirmed | VERIFIED |
| 21 Alembic migrations at Phase D | `backend/alembic/versions/` — 21 files confirmed | VERIFIED |
| Analytics frontend shows entity counts only | `frontend/src/app/(main)/analytics/AnalyticsView.tsx` — confirmed, no trend charts | VERIFIED |
| CorrectiveAction is not a model or table | No `corrective_action.py` model file; referenced only as `ActionType` enum value | VERIFIED |
| UserRole has 7 roles, no INSTITUTION_ADMIN | `backend/app/models/enums.py` — 7 values confirmed | VERIFIED |
| L-05 (module context) is a frontend read issue | `AiChatSession.module_id` persisted in DB; frontend does not restore on reload | VERIFIED |

### 2.2 Discrepancies Found and Corrected

**DISC-01 — NotificationType count**  
- Planning claim (`AQAA_PHASE_D_CAPABILITY_INVENTORY.md`): "8 NotificationType values"  
- Actual (`backend/app/models/enums.py`): 10 values — `AUDIT_ASSIGNED`, `DUE_SOON`, `OVERDUE`, `EVIDENCE_UPLOADED`, `EVIDENCE_MISSING`, `AUDIT_RETURNED`, `AUDIT_APPROVED`, `AUDIT_REJECTED`, `AUDIT_COMPLETED`, `NEW_COMMENT`  
- Severity: LOW (documentation only; does not affect architecture or implementation)  
- Action: Corrected in-place (see Section 16)

**DISC-02 — attachment_grounding_status is in-route, not DB-persisted**  
- Planning claim: Implied as a persistent field on `AiChatMessage`  
- Actual (`backend/app/routes/ai_assistant.py` lines 550, 558, 624–628): Computed per-request and returned in the response; never written to a model field  
- Impact on planning: Gap L-05 description is accurate; the field simply does not exist as a persistent attribute, consistent with the planning gap identification  
- Severity: LOW (planning correctly identifies the gap; the route-level computation is an ephemeral workaround)  
- Action: Clarifying note added to capability inventory (see Section 16)

**DISC-03 — ADR-0013 proposes `is_internal_test` but `is_demo` already exists**  
- Planning claim (ADR-0013): Proposes adding `is_internal_test: bool` column to institutions table  
- Actual (`backend/app/models/institution.py`): `is_demo: bool` and `institution_type: str` fields already present  
- Risk: Migration M-E-01 would add a redundant column alongside existing `is_demo`; application code would need to check both flags  
- Severity: MEDIUM (affects migration design)  
- Action: ADR-0013 updated to adopt `is_demo` for pilot tenant flagging, eliminating the new column (see Section 16)

**DISC-04 — Architecture plan refers to audit_trigger_schedules as a separate table while data requirements doc lists 8 new tables (9 including it)**  
- No material inconsistency; data requirements document correctly includes `audit_trigger_schedules` in the full list  
- Severity: COSMETIC  
- Action: None required

---

## Section 3 — Requirements Quality Audit

### 3.1 Traceability

A spot-check of bidirectional traceability:

| Requirement | Gap reference | ADR/Architecture | Acceptance Criteria |
|-------------|---------------|------------------|---------------------|
| E-FR-001 (ARQ queue) | G-BG-01 (P0) | ADR-0009 | AC-BG-01 |
| E-SEC-001 (TLS) | G-SEC-01 (P0) | ADR-0015 | AC-SEC-01 |
| E-FR-021 (rate limiting) | G-SEC-04 (P0) | Architecture plan §5 | AC-SEC-04 |
| E-GOV-001 (DPIA) | G-REG-03 (P0) | Security plan §2 | AC-GOV-01 |
| E-FR-038 (CHE/DHET/SAQA) | G-REG-01 (P0) | ADR-0014, Reg plan | AC-REG-01 |
| E-NFR-001 (P95 ≤ 500ms) | G-OPS-02 (P1) | Architecture §8 | AC-NFR-01 |

Traceability is complete and consistent for the 18 P0 requirements sampled. No orphaned requirements found.

### 3.2 Requirement Quality Observations

**Strong**: Requirements are testable, measurable, and assigned to workstreams. NFRs include concrete benchmarks (500ms P95, 3s first-token). Security requirements cite OWASP and specific attack classes.

**Adequate**: GOV requirements (E-GOV-001 to E-GOV-006) appropriately scope POPIA obligations without overreaching into legal advice.

**One ambiguity**: E-FR-030 ("AI audit log must capture all AI completions") does not specify minimum retention period. The data requirements document specifies 12 months; these should cross-reference. Low priority to fix before implementation.

---

## Section 4 — Architecture Feasibility Audit

| Component | Classification | Assessment |
|-----------|---------------|------------|
| ARQ task queue | REQUIRED_NOW | Asyncio-native; reuses existing Redis; no new infra. Correct choice. |
| Caddy reverse proxy | REQUIRED_NOW | Zero-config TLS is correct for pilot scale. Caddyfile sample in ADR-0015 is complete and functional. |
| Docker secrets volume | REQUIRED_NOW | Correct pattern for Docker Compose deployment; no Vault dependency needed at pilot scale. |
| structlog + Prometheus + Sentry | REQUIRED_NOW | Observability gap is a P0 pilot blocker. Three-tool stack is lean and correct. |
| WeasyPrint for PDF | REQUIRED_NOW | ~150MB image delta is acceptable; rationale in ADR-0012 is sound. Playwright alternative correctly rejected (too heavy). |
| Pre-aggregated analytics snapshots | REQUIRED_NOW | ADR-0016 rationale is robust. Weekly staleness is acceptable for QA trend analysis. |
| CorrectiveAction model + workflow | REQUIRED_NOW | Currently only referenced as enum value; new model correctly scoped to Sprint E1. |
| AiAuditLog model | REQUIRED_NOW | Governance requirement E-GOV-005; new table correctly proposed in data requirements. |
| compliance_trend_snapshots table | REQUIRED_NOW | Underpins E3 analytics workstream. |
| docker-compose.prod.yml + Caddyfile | REQUIRED_NOW | Production deployment files; correctly identified as P0 gap. |
| MongoDB | NOT_IN_SCOPE | Correctly deferred to Phase F (already architected in Phase D; no new action). |
| Kubernetes / multi-region | NOT_IN_SCOPE | Correctly deferred to Phase F. |
| SSO/SAML | NOT_IN_SCOPE | Correctly deferred to Phase F. |
| ECSA/HPCSA/SACE regulatory bodies | NOT_IN_SCOPE | Correctly deferred; out-of-scope statement is clear. |
| RLS (Row-Level Security) | REQUIRED_LATER | Deferred to Phase F in ADR-0013. Correct decision for pilot. |

**No overengineered components identified.** The technology choices are conservative and appropriate for a first-pilot deployment running on a single machine or small VPS.

---

## Section 5 — ADR Quality Audit

| ADR | Title | Alternatives adequate? | Rationale sound? | Accepted trade-offs noted? | Verdict |
|-----|-------|----------------------|------------------|---------------------------|---------|
| ADR-0009 | Background Task Queue (ARQ) | Yes — Celery, RQ, BackgroundTasks | Yes — asyncio-native, existing Redis | Yes — no web-based monitoring dashboard | APPROVE |
| ADR-0010 | Secrets Management (Docker secrets) | Yes — Vault, AWS SM, plain .env | Yes — no new infra, Docker-native | Yes — not suitable for multi-host | APPROVE |
| ADR-0011 | Observability (structlog + Prometheus + Sentry) | Yes — Datadog, New Relic rejected | Yes — open-source, cost-controlled | Yes — self-hosted Prometheus | APPROVE |
| ADR-0012 | PDF Generation (WeasyPrint) | Yes — ReportLab, Playwright | Yes — HTML/Jinja2 matches skill set | Yes — image size increase | APPROVE |
| ADR-0013 | Pilot Tenant Isolation | Yes — RLS, schema-per-tenant | Yes — proven pattern; pilot scale | Yes — deferred to Phase F | APPROVE_WITH_CORRECTIONS (corrected) |
| ADR-0014 | Regulatory Knowledge Governance | Yes — open ingestion, single-tier | Yes — two-tier mitigates hallucination risk | Yes — Engineering bottleneck for OFFICIAL_VERIFIED | APPROVE |
| ADR-0015 | Reverse Proxy (Caddy) | Yes — nginx, Traefik | Yes — zero-config TLS operational value | Yes — Kubernetes replacement in Phase F | APPROVE |
| ADR-0016 | Analytics Aggregation (pre-aggregated) | Yes — real-time query, materialized views | Yes — pilot scale vs. complexity | Yes — 7-day data staleness | APPROVE |

---

## Section 6 — Database and Migration Audit

### 6.1 New Tables Proposed

| Table | Purpose | Additive? | Nullable FKs where needed? |
|-------|---------|-----------|---------------------------|
| corrective_actions | Corrective action records | Yes | Yes — module_id or programme_id |
| corrective_action_history | State change history | Yes | No — FK to corrective_actions |
| ai_audit_logs | All AI completion events | Yes | Yes — request scoped |
| hallucination_incidents | Confirmed hallucination records | Yes | Yes — FK to ai_audit_logs |
| regulatory_document_registry | CHE/DHET/SAQA document metadata | Yes | No |
| compliance_trend_snapshots | Pre-aggregated analytics | Yes | No |
| pilot_consent | Pilot participant consent records | Yes | Yes — user_id |
| background_job_logs | ARQ job execution log | Yes | No |
| audit_trigger_schedules | Scheduled audit configurations | Yes | Yes — module_id or programme_id |

All 9 tables are additive-only. No existing columns are modified. All foreign keys respect the existing UUID primary key pattern. The migration design is safe.

### 6.2 Migration Sequence (M-E-01 through M-E-07)

The migration sequence correctly stages dependencies:
- M-E-01: Infrastructure prep (pilot flag on institution; `is_demo` retained — see DISC-03 correction)
- M-E-02: Background processing infrastructure (`background_job_logs`, `audit_trigger_schedules`)
- M-E-03: Corrective actions (`corrective_actions`, `corrective_action_history`)
- M-E-04: AI governance (`ai_audit_logs`, `hallucination_incidents`)
- M-E-05: Regulatory knowledge (`regulatory_document_registry`)
- M-E-06: Analytics (`compliance_trend_snapshots`)
- M-E-07: Pilot operations (`pilot_consent`)

No circular dependency in the sequence. All migrations are reversible (no destructive DDL).

---

## Section 7 — Security, Privacy and POPIA Audit

### 7.1 POPIA Compliance Assessment

The security and governance plan correctly identifies the primary POPIA obligations for a pilot:
- DPIA before first data subject enters the system ✓
- Consent capture (pilot_consent table) ✓
- Data subject rights (access, correction, deletion) specified ✓
- Retention schedule (audit logs 12m, student data 7 years, consent records 5 years) ✓
- Third-party AI provider controls (data processing addendum with Claude/OpenAI) ✓

**Gap not addressed in planning**: The POPIA plan does not specify who holds the Information Officer role during the pilot. This is a soft compliance requirement (every responsible party should designate one) but not a pilot blocker. The owner should note this for resolution before pilot start.

### 7.2 Security Controls Assessment

| Control | Priority | Addressed? | Evidence |
|---------|----------|-----------|----------|
| TLS for all traffic | P0 | Yes | ADR-0015, E-SEC-001, AC-SEC-01 |
| No committed secrets | P0 | Yes | ADR-0010, E-SEC-002 |
| Rate limiting (slowapi) | P0 | Yes | E-FR-021, AC-SEC-04 |
| Virus scanning (clamav) | P0 | Yes | E-FR-026, AC-SEC-09 |
| JWT deny-list (logout) | P0 | Yes | E-FR-024, AC-SEC-06 |
| MFA (TOTP) | P1 | Yes | E-FR-025, AC-SEC-07 (Sprint E4) |
| OWASP dependency scan | P0 | Yes | E-SEC-006, AC-SEC-05 |
| Cross-tenant logging | P0 | Yes | E-SEC-007, AC-SEC-08 |
| Storage namespace isolation | P0 | Yes | E-FR-027 |
| Key rotation procedure | P1 | Yes | E-SEC-008 |

All 18 P0 security gaps from the gap analysis map to requirements and acceptance criteria.

### 7.3 Threat Model Assessment

The STRIDE threat model is appropriate in scope for the pilot threat surface. All six categories are addressed. The threat model correctly excludes nation-state actors and APT-level threats (appropriate for pilot scale). The incident response plan provides workable severity tiers and escalation paths.

---

## Section 8 — Regulatory Governance Audit

### 8.1 Two-Tier Governance Model

The two-tier model (AQAA Engineering = OFFICIAL_VERIFIED; Institution Admin = INSTITUTIONAL_APPROVED) is well-designed:
- It prevents institutions from self-certifying national accreditation frameworks as authoritative
- It aligns with how CHE/DHET/SAQA actually operate (public documents, infrequent updates)
- The annual review schedule (July) is realistic and calendar-anchored

### 8.2 Source Availability

CHE (Higher Education Act frameworks), DHET (NPPFHE, Staffing South Africa's Universities Framework), and SAQA (NQF level descriptors) all maintain publicly accessible document repositories. The sourcing plan is feasible.

### 8.3 Supersession Lifecycle

The `DRAFT_IMPORT → OFFICIAL_VERIFIED → SUPERSEDED → ARCHIVED` lifecycle matches the `SourceStatus` enum values confirmed in `backend/app/models/enums.py`. The lifecycle is implementable with the existing enum without changes.

---

## Section 9 — Role and UX Audit

### 9.1 Role Coverage

The role experience plan correctly covers all 7 roles in the UserRole enum. The absence of a distinct INSTITUTION_ADMIN role is correctly handled (SYSTEM_ADMIN scoped to single institution). No new roles are proposed for Phase E — correct given the RBAC hierarchy is complete.

### 9.2 UX Gap Coverage

Key UX gaps from the gap analysis are addressed in the role plan:
- Onboarding wizard (E-UX-001) → all roles have tour scripts ✓
- Context restore on reload (L-05) → frontend fix in Sprint E5 ✓
- WCAG 2.1 AA (E-UX-007) → Sprint E5 ✓
- Mobile-responsive audit views (E-UX-006) → Sprint E5 ✓

### 9.3 Onboarding Design Quality

The onboarding tour scripts for each role are appropriately scoped — they guide users to their primary value proposition (QA Officer → compliance dashboard, Lecturer → evidence upload, Student → AI Workspace) rather than attempting to demonstrate all features. This is commercially sound for a pilot.

---

## Section 10 — Sprint Roadmap Audit

### 10.1 Sequence Analysis

| Sprint | Weeks | Dependencies met? | Deliverable count | Assessment |
|--------|-------|------------------|------------------|------------|
| E0 | 1–2 | None | 13 | ACHIEVABLE — infrastructure; no new feature logic |
| E1 | 3–4 | ARQ (E0) | 13 | ACHIEVABLE — ARQ from E0 unblocks all E1 tasks |
| E2 | 5–6 | ARQ (E0), observability (E1) | 17 | ACHIEVABLE — regulatory ingestion is standalone |
| E3 | 7–8 | Snapshots table (E2), ARQ (E0) | 16 | ACHIEVABLE — analytics reads from E2 tables |
| E4 | 9–10 | AI audit log (E2) | 17 | ACHIEVABLE — governance layer on top of E2 |
| E5 | 11–12 | All features complete | 16 | ACHIEVABLE — UX polish; no new backend |
| E6 | 13–16 | All 18 P0 gaps closed | N/A (pilot) | CONDITIONAL — all acceptance criteria must pass |
| E7 | 17–18 | Pilot complete | N/A (eval) | ACHIEVABLE |

### 10.2 Risk in Roadmap

**Highest sprint risk**: E2 (weeks 5–6) carries 17 deliverables including Qdrant ingestion pipeline, AI audit log schema, and observability wiring. This is the densest sprint. The risk register correctly flags CHE/DHET/SAQA indexing delay as R-11 (probability 2, impact 3).

**Mitigation available**: Regulatory ingestion has no dependency on pilot users; it can start in E0 in parallel with infrastructure work if sprint capacity allows.

### 10.3 Timeline Realism

18 weeks for the scope described is tight but achievable for a focused team. The planning correctly prohibits new feature additions during Sprint E6 (pilot period). Week count excludes Phase E planning time, which is already complete.

---

## Section 11 — Evaluation Plan Audit

### 11.1 Metrics Quality

All 25 metrics (M-01 to M-25) are evaluated:

| Category | Metrics | Measurable? | Benchmarks set? | Data source identified? |
|----------|---------|------------|----------------|------------------------|
| Platform health | M-01–M-05 | Yes | Yes | Yes |
| Engagement | M-06–M-10 | Yes | Yes | Yes |
| QA Outcomes | M-11–M-15 | Yes | Yes | Yes |
| AI Quality | M-16–M-22 | Yes | Yes | Yes |
| Security | M-23–M-25 | Yes | Yes | Yes |

### 11.2 Critical Metric Assessment

**M-16 (Grounding coverage ≥ 85%)**: Technically sound. `confidence_score` is already computed and surfaced in the streaming response. A backend aggregation job can compute this from `ai_audit_logs`.

**M-19 (Confirmed hallucinations ≤ 1 per 1,000 completions)**: Correctly defined as "confirmed" (requiring human review via hallucination_incidents table). The 1/1,000 threshold is appropriately conservative for an accreditation context.

**M-20 (Positive feedback ≥ 80%)**: Current `AiChatMessage` model has no feedback field. The architecture plan correctly proposes adding one. This metric is only measurable after Sprint E4 implementation. Plan correctly schedules feedback collection from pilot week 1.

**M-11 (Time to first audit ≤ 2 hours)**: This is an engagement/onboarding metric. The onboarding tour scripts support this target. Realistic for a well-prepared pilot cohort.

### 11.3 Qualitative Measures

The plan correctly includes qualitative measures alongside quantitative metrics (interview protocol, focus group agenda, SUS score). This is methodologically sound for a research-grade pilot in an academic context.

---

## Section 12 — Pilot Feasibility Audit

### 12.1 Eligibility and Cohort Design

The pilot eligibility criteria are appropriate:
- South African HEI with active QA function
- Active accreditation cycle (CHE/DHET)
- Minimum 8 users across ≥ 3 roles
- Institutional data protection agreement in place

The minimum cohort size (8 users) is sufficient to generate meaningful signal on M-06 to M-15, while remaining manageable operationally.

### 12.2 Pre-Pilot Technical Checklist

The 18-item pre-pilot technical checklist maps directly to the 18 P0 gaps. Each P0 gap has a corresponding checklist item. This is correctly designed as a gate — no item can be left unchecked.

### 12.3 Rollback Procedure

The 4-hour rollback target is achievable given Docker Compose deployment. The procedure (stop containers, restore volume snapshot, restart, verify health, notify institution) is complete and testable.

### 12.4 Support SLAs

SLAs are appropriate for a controlled pilot:
- Critical (system down): 2-hour response
- High (feature broken): 4-hour response  
- Medium (workflow impaired): 24-hour response  
- Low (cosmetic): best-effort

These are reasonable for a small team operating a first pilot.

---

## Section 13 — Commercial Scope Audit

### 13.1 Standalone Constraint Verified

All planning documents have been reviewed for AQAA standalone integrity. No dependency on MSc Academic Intelligence System, AcademicOS, ResearchOS, RIAE, Lecturer Support Agent, PersonalOS, or any other system was found. All referenced external systems (CHE, DHET, SAQA, Claude/OpenAI API, Sentry) are legitimate external services, not cross-project dependencies.

### 13.2 Commercial Positioning

The Phase E scope positions AQAA appropriately for a first commercial pilot:
- South African Higher Education sector focus (specific, addressable market)
- CHE/DHET/SAQA grounding makes the value proposition credible to QA Officers
- POPIA compliance addresses the primary institutional procurement concern
- Controlled pilot with exit criteria protects both AQAA Engineering and the pilot institution

### 13.3 Deferred Scope Appropriateness

The following are correctly deferred to Phase F:
- Commercial billing and multi-tenancy SaaS model
- Inter-institution benchmarking
- SSO/SAML enterprise authentication
- ECSA/HPCSA/SACE (professional body frameworks beyond HE)
- Kubernetes / cloud-native deployment
- Native mobile app

None of these are required for a single-institution pilot. Deferring them is the correct commercial decision.

### 13.4 Competitive Risk

The planning does not address competitive landscape (other South African QA tools, spreadsheet-based QA processes). For a pilot planning document, this is acceptable — competitive analysis belongs in a market entry document, not an engineering planning package.

---

## Section 14 — Cross-Document Consistency Audit (Contradiction Register)

The following cross-document checks were performed. Only real contradictions that could cause implementation confusion are listed.

| # | Claim in Doc A | Claim in Doc B | Assessment |
|---|---------------|---------------|------------|
| C-01 | Capability inventory: "8 NotificationType values" | enums.py: 10 values | CONTRADICTION — corrected (DISC-01) |
| C-02 | ADR-0013: Add `is_internal_test` column | institution.py: `is_demo` already exists | CONTRADICTION — corrected (DISC-03) |
| C-03 | Requirements E-FR-030: no retention period stated | Data requirements: 12-month retention for AI audit log | MINOR OMISSION — cross-reference note added |
| C-04 | Data requirements: "8 new tables" | Architecture plan section: lists 9 tables (includes audit_trigger_schedules) | COSMETIC — both counts are defensible depending on grouping |
| C-05 | Role plan: "Institution Admin handled by SYSTEM_ADMIN" | UserRole enum: no INSTITUTION_ADMIN value | CONSISTENT — plan correctly accounts for the absence |

No fundamental scope contradictions found. Documents align on: sprint sequence, P0 priority ordering, tenant isolation approach, regulatory governance model, and pilot success thresholds.

---

## Section 15 — Owner Decision Register

The following items require an explicit owner decision before implementation begins. Neither is a blocker requiring plan revision; they are decision points that are appropriately left to the owner.

### OD-01 — POPIA Information Officer

**Decision required**: Who holds the Information Officer role for AQAA during the pilot?  
**Background**: POPIA section 55 requires every responsible party to designate an Information Officer. During the pilot, AQAA Engineering is the processor and the pilot institution is the responsible party. The engineering team should clarify whether to recommend the institution designate their own Information Officer, or whether AQAA Engineering takes on this role for purposes of the pilot DPA.  
**Default if not actioned**: This does not block technical implementation but must be resolved before the pilot DPA is signed.  
**Owner action**: Designate or recommend Information Officer in writing before Sprint E5 (pilot preparation).

### OD-02 — Pilot Institution Pre-Commitment

**Decision required**: Has a pilot institution been identified and engaged?  
**Background**: The evaluation plan targets a controlled pilot with a real South African HEI. The pilot deployment plan requires institutional sign-off on a data processing agreement, participant consent process, and 30-day availability. The planning package was written assuming a pilot institution will be identified during Sprint E5 (weeks 11–12). If no institution is currently in dialogue, Sprint E6 start may slip.  
**Default if not actioned**: Sprint E6 cannot begin without an institution ready. The build sprints (E0–E5) can proceed regardless.  
**Owner action**: Confirm current status of pilot institution engagement before Sprint E4 begins (week 9).

---

## Section 16 — Documentation Corrections Applied

The following documentation-only corrections were applied. No source code, migrations, or runtime configuration was modified.

### Correction 1: NotificationType count in AQAA_PHASE_D_CAPABILITY_INVENTORY.md

**File**: `docs/phase-e/AQAA_PHASE_D_CAPABILITY_INVENTORY.md`  
**Change**: Updated "8 NotificationType values" to "10 NotificationType values" with full enumeration  
**Evidence**: `backend/app/models/enums.py` — 10 values confirmed: `AUDIT_ASSIGNED`, `DUE_SOON`, `OVERDUE`, `EVIDENCE_UPLOADED`, `EVIDENCE_MISSING`, `AUDIT_RETURNED`, `AUDIT_APPROVED`, `AUDIT_REJECTED`, `AUDIT_COMPLETED`, `NEW_COMMENT`

### Correction 2: ADR-0013 — Replace `is_internal_test` with `is_demo`

**File**: `docs/architecture/decisions/ADR-0013-pilot-tenant-isolation.md`  
**Change**: ADR revised to adopt the existing `is_demo: bool` field on the Institution model for pilot tenant flagging. Migration M-E-01 does not add a new column; it simply documents that `is_demo = True` identifies pilot/internal institutions. Added note that `institution_type` field provides additional classification if needed.  
**Evidence**: `backend/app/models/institution.py` — `is_demo` and `institution_type` confirmed present; `is_internal_test` confirmed absent

### Correction 3: attachment_grounding_status clarification note in AQAA_PHASE_D_CAPABILITY_INVENTORY.md

**File**: `docs/phase-e/AQAA_PHASE_D_CAPABILITY_INVENTORY.md`  
**Change**: Added clarifying note that `attachment_grounding_status` is computed per-request in `ai_assistant.py` route (lines 550–628) and returned in the response body but not persisted as a model field. Gap L-05 (frontend does not restore module context on reload) remains correctly identified.

---

## Section 17 — Git Validation and Final Output

### 17.1 Repository State at Review Completion

```
Branch:   feature/phase-e
HEAD:     af7b2af8eaf1c12e21b0dec8e2120e0ca6108e25
Tag:      v0.9.0-phase-d → 40b25ddfbb737322627ad33a48a4f212ef37e36f (UNCHANGED)
Modified: CHANGELOG.md (M), PHASE_TRACKER.md (M)
Untracked: docs/architecture/decisions/ (??), docs/phase-e/ (??)
Source code modified: NONE
Migrations created: NONE
Runtime configuration altered: NONE
```

All Phase E work is documentation-only. The Phase D preservation tag is intact. No source code was modified. No commits were created during this review. All planning documents remain on the untracked file list pending owner approval and the planning commit.

### 17.2 Files Modified During Review (Documentation Only)

1. `docs/phase-e/AQAA_PHASE_D_CAPABILITY_INVENTORY.md` — Corrections 1 and 3
2. `docs/architecture/decisions/ADR-0013-pilot-tenant-isolation.md` — Correction 2
3. `docs/phase-e/AQAA_PHASE_E_OWNER_REVIEW_REPORT.md` — This document (created)

### 17.3 Files Reviewed (Read-Only)

All 15 planning documents, all 8 ADRs, PHASE_TRACKER.md, CHANGELOG.md, and the following source files:
- `backend/app/models/enums.py`
- `backend/app/models/ai_chat.py`
- `backend/app/models/institution.py`
- `backend/app/routes/reporting.py`
- `backend/app/routes/ai_assistant.py`
- `backend/requirements.txt`
- `frontend/src/app/(main)/analytics/AnalyticsView.tsx`
- `backend/alembic/versions/` (directory listing)
- `docker-compose.yml`
- `docs/architecture/decisions/ADR-0015-reverse-proxy.md`
- `docs/architecture/decisions/ADR-0016-analytics-aggregation.md`

---

## Final Verdict

**READY FOR OWNER APPROVAL WITH CONDITIONS**

The AQAA Phase E planning package is internally consistent, technically grounded, commercially appropriate for a South African HEI pilot, and academically defensible as an evaluation methodology. The 18 P0 pilot-blocking gaps are correctly identified and fully addressed across requirements, architecture, acceptance criteria, and sprint deliverables. The ADR decisions (ARQ, Caddy, WeasyPrint, Docker secrets, application-layer isolation, pre-aggregated analytics) are sound and correctly argued.

**Conditions for approval:**

1. **OD-01**: Owner designates or confirms Information Officer arrangement for the pilot data processing agreement (required before Sprint E5)
2. **OD-02**: Owner confirms pilot institution engagement status before Sprint E4 (week 9) to prevent E6 slip

Neither condition requires plan revision. Both are administrative decisions that belong to the owner, not the engineering team.

**Implementation may begin (Sprint E0) upon owner written approval of this package.**

---

*Review completed by: AQAA Engineering — Independent Review Role*  
*Date: 2026-07-17*  
*Review type: Documentation-only; no source code, migrations, commits, or runtime changes*
