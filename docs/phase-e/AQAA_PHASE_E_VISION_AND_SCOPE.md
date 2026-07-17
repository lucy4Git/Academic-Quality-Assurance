# AQAA Phase E — Vision and Scope

**Phase Title:** Autonomous Quality Intelligence, Institutional Deployment and Continuous Improvement
**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Baseline:** Phase D (v0.9.0-phase-d)
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Vision Statement

Phase E transforms AQAA from a manually triggered audit platform into a continuously observing, autonomously reporting quality intelligence system capable of operating as the institutional QA backbone for South African higher education institutions. By the end of Phase E, AQAA will be deployable to real institutions under pilot conditions, with verified regulatory grounding, production-grade security, and role-differentiated AI experiences that make every stakeholder — from Dean to Lecturer — materially more effective in discharging their quality assurance obligations.

---

## 2. Strategic Objectives

| # | Objective | Success Condition |
|---|-----------|------------------|
| E-OBJ-01 | Resolve all P0 pilot-blocking gaps before first live tenant | All 18 P0 gaps from commercial gap analysis closed |
| E-OBJ-02 | Deploy and run a controlled pilot at minimum one institution | Pilot cohort active, consent collected, lessons-learned complete |
| E-OBJ-03 | Index verified regulatory documents for CHE, DHET, SAQA | `source_status = OFFICIAL_VERIFIED` on at least 3 frameworks |
| E-OBJ-04 | Implement autonomous compliance monitoring | Background scheduler triggers audits without manual initiation |
| E-OBJ-05 | Deliver production-grade analytics and PDF/DOCX export | Export pipeline functional; trend charts live in dashboard |
| E-OBJ-06 | Achieve POPIA compliance baseline | DPIA completed; data retention schedule implemented |
| E-OBJ-07 | Establish AI governance controls | AI output audit log; hallucination incident register; grounding coverage ≥ 85% |
| E-OBJ-08 | CI/CD pipeline operational | Every push runs full test suite; build/deploy automated |
| E-OBJ-09 | WCAG 2.1 AA compliance verified | Third-party accessibility audit passed or internal audit complete with no P1 failures |

---

## 3. Phase E Workstreams

| ID | Workstream | Owner Domain | Phase E Milestone |
|----|------------|-------------|------------------|
| E1 | Autonomous Monitoring and Workflow Engine | Backend | Sprint E2–E4 |
| E2 | Verified Regulatory Knowledge | AI / RAG | Sprint E1–E3 |
| E3 | Analytics, Reporting and Export | Backend + Frontend | Sprint E2–E4 |
| E4 | Production Security and Hardening | Platform | Sprint E0–E2 |
| E5 | AI Governance and Accountability | AI / Platform | Sprint E2–E4 |
| E6 | DevOps, CI/CD and Operations | Infrastructure | Sprint E0–E2 |
| E7 | Pilot Deployment and User Experience | Product | Sprint E3–E7 |

---

## 4. In Scope for Phase E

### Platform and Security
- TLS termination and HTTPS enforcement in Docker Compose and production config
- Secrets management (Vault or equivalent)
- Rate limiting on all API endpoints
- Virus scanning (ClamAV) enabled with configurable mode
- Environment separation: development, staging, production configurations
- JWT revocation list / session invalidation on logout
- MFA (TOTP-based, not SMS) for QA Officers and above
- Storage path tenant namespacing
- Automated daily database backup (pg_dump to configurable destination)
- Automated Qdrant snapshot schedule

### Background Processing
- Task queue (ARQ or Celery) with Redis as broker
- Scheduled audit triggers: daily, weekly, per-institution schedule
- Background task persistence and visibility
- Retry with exponential backoff

### Regulatory Knowledge
- CHE HEQSF standards indexed as OFFICIAL_VERIFIED
- DHET Policy on the Minimum Requirements for Teacher Education Qualifications indexed
- SAQA NQF descriptor documents indexed
- Institutional policy document upload and indexing workflow
- Regulatory document version management (superseded tracking)

### Analytics and Reporting
- Compliance trend charts (12-month rolling window)
- Faculty-level compliance heat map
- Audit cycle comparison (period-over-period)
- PDF export (real implementation, replacing placeholder)
- DOCX export for audit reports
- XLSX export for raw finding data

### AI Governance
- Immutable AI output audit log (what was asked, what was answered, what sources were cited)
- Hallucination incident capture: AI response flag mechanism for QA Officers
- Grounding coverage metric: % of responses with ≥1 OFFICIAL_VERIFIED citation
- Per-tenant AI cost monitoring

### Corrective Action Workflow
- `CorrectiveAction` model with due date, assignee, status, evidence-of-resolution
- Automated overdue notification (in-app, with SMTP email when configured)
- CAP template generator in AI Workspace

### Pilot Deployment
- Tenant provisioning API and guided admin onboarding wizard
- IKP auto-setup for new institutions
- Pilot consent and data governance pack
- Pilot monitoring dashboard for AQAA Engineering
- Pilot exit criteria and lessons-learned protocol

### DevOps
- GitHub Actions CI pipeline: test, build, lint on every push
- Production Docker Compose (separate from dev)
- Staging environment configuration
- Resource limits in Docker Compose
- Rollback automation script

### User Experience
- Module context restoration on page reload (L-05)
- WCAG 2.1 AA audit and remediation
- User onboarding tour (first-login guided flow)
- Role-specific dashboard enhancements: Dean, HOD heat maps
- Faculty compliance heat map component

### Observability
- Structured JSON logging with correlation IDs
- Prometheus metrics endpoint
- Sentry integration (error tracking)
- Per-tenant usage dashboard for system administrators

---

## 5. Out of Scope for Phase E

The following items are explicitly excluded from Phase E. They may be revisited in future phases.

| Excluded Item | Reason |
|--------------|--------|
| MongoDB integration | Architecturally reserved; no use case in Phase E scope |
| ECSA, HPCSA, SACE framework indexing | Specialist regulatory frameworks; deferred to Phase F |
| Real-time multi-user collaboration on AI sessions | Single-user session model retained |
| SSO / SAML integration | Deferred to Phase F (enterprise identity) |
| Kubernetes production deployment | Docker Compose sufficient for pilot scale |
| Native mobile app | Web-responsive retained; no native app |
| Student-facing QA features | Student role remains limited observer |
| Inter-institution benchmarking | Insufficient comparative data during pilot |
| Commercial billing / subscription management | Not required for pilot |
| QCTO occupational qualifications indexing | Deferred unless pilot institution requires it |

---

## 6. Phase E Constraints

1. **Standalone project**: AQAA must remain completely standalone. No dependency on MSc Academic Intelligence System, ResearchOS, RIAE, Lecturer Support Agent, PersonalOS, or any other project.
2. **No backwards-incompatible API changes** without migration plan and version bump.
3. **Phase D tag `v0.9.0-phase-d` must not be modified or disturbed.**
4. **POPIA compliance**: All pilot data must be handled per South African POPIA requirements. No real student records in development or test data.
5. **Budget constraint**: Pilot infrastructure must operate on a single server or cloud instance — no multi-region deployment.
6. **Regulatory document sourcing**: Only documents with verifiable public availability may be indexed. No proprietary or fee-gated documents without written permission.

---

## 7. Success Criteria

### Phase E Exit Criteria (all must pass before Phase E tag)

| Criterion | Measurement |
|-----------|-------------|
| All 18 P0 gaps closed | Commercial gap analysis P0 column all marked CLOSED |
| Backend test suite ≥ 1,319 tests, 0 failures | `python -m pytest -q` |
| TypeScript 0 errors | `tsc --noEmit` |
| Production build clean | `npm run build` |
| Pilot completed | At least 1 institution onboarded, 30-day pilot run, exit survey completed |
| OFFICIAL_VERIFIED coverage | CHE, DHET, SAQA indexed; ≥ 3 frameworks |
| PDF export functional | Real implementation, not placeholder |
| CI pipeline operational | GitHub Actions green on main branch |
| AI grounding coverage | ≥ 85% of QA Officer workspace queries cite ≥1 OFFICIAL_VERIFIED source |
| WCAG 2.1 AA | Internal audit: 0 Level A failures, ≤ 5 Level AA non-critical failures |
| POPIA baseline | DPIA documented and reviewed |

---

## 8. Relationship to Phase D

Phase E directly addresses every Phase D known limitation and all 91 commercial gaps documented in the gap analysis. The Phase D AI Workspace, finding lifecycle, multi-tenancy, RBAC, and regulatory framework engine are all retained and extended — not replaced. Phase E adds the production substrate and regulatory depth required to move from a technically complete development baseline to a pilot-deployable institutional system.

---

## Referenced Documents

- [AQAA_PHASE_D_CAPABILITY_INVENTORY.md](AQAA_PHASE_D_CAPABILITY_INVENTORY.md)
- [AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md](AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md)
- [AQAA_PHASE_E_SPRINT_ROADMAP.md](AQAA_PHASE_E_SPRINT_ROADMAP.md)
- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md)
