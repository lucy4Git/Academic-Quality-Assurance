# AQAA Phase E — Master Index

**Phase Title:** Autonomous Quality Intelligence, Institutional Deployment and Continuous Improvement  
**Approval date:** 2026-07-17  
**Branch:** `feature/phase-e`  
**Status:** APPROVED_WITH_CONDITIONS  
**Sprint E0:** AUTHORIZED  
**Implementation:** 0% (planning only; no source code, migration, or runtime change)

> All planning documents are marked APPROVED_WITH_CONDITIONS. Implementation depends on the resolution of conditions OD-01 and OD-02 where specified. Proposed ADRs remain PROPOSED until individually confirmed during implementation.

---

## Phase Context

| Item | Value |
|------|-------|
| Phase D tag | `v0.9.0-phase-d` → commit `40b25dd` |
| Phase D status | MERGED_AND_PRESERVED |
| Phase E branch | `feature/phase-e` |
| Phase E planning commit | Pending push — pending PR merge to main |
| Phase E target tag | `v1.0.0-phase-e` (on completion) |
| Approval document | [AQAA_PHASE_E_OWNER_APPROVAL.md](AQAA_PHASE_E_OWNER_APPROVAL.md) |
| Review document | [AQAA_PHASE_E_OWNER_REVIEW_REPORT.md](AQAA_PHASE_E_OWNER_REVIEW_REPORT.md) |

---

## Approval Conditions

| Condition | Status | Due gate |
|-----------|--------|----------|
| OD-01: Information Officer and data-processing governance | OPEN | Before Sprint E5; before any real institutional data |
| OD-02: Pilot institution engagement confirmed | OPEN | Before Sprint E4 (week 9) |

---

## Planning Documents

| # | Document | Status | Approval date | Implementation dependency |
|---|----------|--------|---------------|--------------------------|
| 1 | [AQAA_PHASE_D_CAPABILITY_INVENTORY.md](AQAA_PHASE_D_CAPABILITY_INVENTORY.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | None (reference document) |
| 2 | [AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md](AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | None (reference document) |
| 3 | [AQAA_PHASE_E_VISION_AND_SCOPE.md](AQAA_PHASE_E_VISION_AND_SCOPE.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | None |
| 4 | [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E0+ |
| 5 | [AQAA_PHASE_E_ARCHITECTURE_PLAN.md](AQAA_PHASE_E_ARCHITECTURE_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Each ADR confirmed per sprint |
| 6 | [AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md](AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E0 (security controls) |
| 7 | [AQAA_PHASE_E_DATA_REQUIREMENTS.md](AQAA_PHASE_E_DATA_REQUIREMENTS.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Each migration per sprint |
| 8 | [AQAA_PHASE_E_REGULATORY_KNOWLEDGE_PLAN.md](AQAA_PHASE_E_REGULATORY_KNOWLEDGE_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E2 (E5 workstream) |
| 9 | [AQAA_PHASE_E_ROLE_EXPERIENCE_PLAN.md](AQAA_PHASE_E_ROLE_EXPERIENCE_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E5 (UX) |
| 10 | [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E6 (pilot) |
| 11 | [AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md](AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | OD-01 and OD-02 required |
| 12 | [AQAA_PHASE_E_RISK_REGISTER.md](AQAA_PHASE_E_RISK_REGISTER.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Live document — update each sprint |
| 13 | [AQAA_PHASE_E_SPRINT_ROADMAP.md](AQAA_PHASE_E_SPRINT_ROADMAP.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Sprint E0 begins post-push |
| 14 | [AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md](AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | Gate-tested per sprint |
| 15 | [00_AQAA_PHASE_E_INDEX.md](00_AQAA_PHASE_E_INDEX.md) | APPROVED_WITH_CONDITIONS | 2026-07-17 | This document |

---

## Architecture Decision Records (Phase E Proposed)

All ADRs remain **PROPOSED**. Owner approval of the planning package does not constitute acceptance. Each ADR is confirmed individually during the relevant sprint.

| ADR | Title | Status | Relevant sprint |
|-----|-------|--------|----------------|
| [ADR-0009](../architecture/decisions/ADR-0009-background-task-queue.md) | Background Task Queue (ARQ) | PROPOSED | E0 |
| [ADR-0010](../architecture/decisions/ADR-0010-secrets-management.md) | Secrets Management (Docker secrets) | PROPOSED | E0 |
| [ADR-0011](../architecture/decisions/ADR-0011-observability-approach.md) | Observability (structlog + Prometheus + Sentry) | PROPOSED | E0 |
| [ADR-0012](../architecture/decisions/ADR-0012-pdf-generation-library.md) | PDF Generation (WeasyPrint) | PROPOSED | E3 |
| [ADR-0013](../architecture/decisions/ADR-0013-pilot-tenant-isolation.md) | Pilot Tenant Isolation (is_demo existing field) | PROPOSED | E0 |
| [ADR-0014](../architecture/decisions/ADR-0014-regulatory-knowledge-governance.md) | Regulatory Knowledge Governance | PROPOSED | E2 |
| [ADR-0015](../architecture/decisions/ADR-0015-reverse-proxy.md) | Reverse Proxy (Caddy) | PROPOSED | E0 |
| [ADR-0016](../architecture/decisions/ADR-0016-analytics-aggregation.md) | Analytics Aggregation (pre-aggregated snapshots) | PROPOSED | E3 |

---

## Governance and Validation Documents

| Document | Purpose |
|----------|---------|
| [AQAA_PHASE_E_OWNER_REVIEW_REPORT.md](AQAA_PHASE_E_OWNER_REVIEW_REPORT.md) | Independent 17-section review; verdict READY FOR OWNER APPROVAL WITH CONDITIONS; 4 discrepancies found and resolved |
| [AQAA_PHASE_E_OWNER_APPROVAL.md](AQAA_PHASE_E_OWNER_APPROVAL.md) | Formal owner approval; records OD-01, OD-02, governance boundaries, sprint authorization |
| [AQAA_PHASE_E_TRACEABILITY_VALIDATION.md](AQAA_PHASE_E_TRACEABILITY_VALIDATION.md) | Pre-commit traceability validation; result: PASS |

---

## Key Decisions Recorded in This Package

| Decision | Where recorded |
|----------|---------------|
| 18 P0 gaps must close before pilot | Commercial gap analysis, acceptance criteria |
| Pilot institution engagement is a condition (OD-02) | Owner approval; review report |
| POPIA / Information Officer is a condition (OD-01) | Owner approval; security plan |
| All ADRs remain PROPOSED | Owner approval §Decision 4 |
| Autonomous action boundaries | Owner approval §Decision 5 |
| Tenant isolation requirements | Owner approval §Decision 6 |
| ARQ over Celery | ADR-0009 |
| Caddy over nginx | ADR-0015 |
| WeasyPrint for PDF | ADR-0012 |
| Docker secrets pattern | ADR-0010 |
| Application-layer isolation retained (is_demo) | ADR-0013 |
| Pre-aggregated analytics snapshots | ADR-0016 |
| Two-tier regulatory governance | ADR-0014 |
| Phase F scope | Vision and scope, owner approval deferred decisions |

---

## Approved Workstreams

| Workstream | Description | Sprint | Status |
|------------|-------------|--------|--------|
| E0 | Infrastructure foundation | Sprint E0 | AUTHORIZED |
| E1 | Production-readiness foundation | Sprint E1 | NOT_STARTED |
| E2 | Autonomous quality monitoring | Sprint E2 | NOT_STARTED |
| E3 | Workflow and remediation automation | Sprint E3 | NOT_STARTED |
| E4 | Institutional analytics and executive intelligence | Sprint E4 | NOT_STARTED |
| E5 | Regulatory knowledge governance | Sprint E5 | NOT_STARTED |
| E6 | Pilot deployment and onboarding | Sprint E6 | NOT_STARTED |
| E7 | Evaluation and continuous improvement | Sprint E7 | NOT_STARTED |

---

## What This Package Does NOT Include

- Source code implementation of any Phase E feature
- Database migrations
- Commits to main branch (pending PR review and merge)
- Any modification to the Phase D tag `v0.9.0-phase-d`
- Feature flags, backwards-compatibility shims, or placeholder implementations
- Authorization to process real institutional or personal data (requires OD-01)
- Confirmation that any named institution has agreed to be a pilot participant

---

**Prepared by:** AQAA Engineering  
**Date:** 2026-07-17  
**Review:** Independent architecture and governance review — READY FOR OWNER APPROVAL WITH CONDITIONS  
**Owner decision:** APPROVED_WITH_CONDITIONS  
**Sprint E0:** AUTHORIZED
