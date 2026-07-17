# AQAA Phase E — Commercial Gap Analysis

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Branch:** feature/phase-e
**Baseline:** Phase D (v0.9.0-phase-d)
**Status:** APPROVED_WITH_CONDITIONS

> Priority codes: **P0** = pilot blocker (must be resolved before any live tenant); **P1** = commercial launch blocker; **P2** = commercial competitive gap; **P3** = future enhancement.

---

## 1. Security and Compliance Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| SEC-01 | No rate limiting on any API endpoint | All endpoints unlimited | P0 | E4 (Security) |
| SEC-02 | No HTTPS enforcement in Docker Compose | HTTP only in dev | P0 | E4 |
| SEC-03 | Secrets management via `.env` file only | No Vault, no Secrets Manager | P0 | E4 |
| SEC-04 | Virus scanning disabled (`VIRUS_SCAN_ENABLED=False`) | ClamAV hook present, disabled | P0 | E4 |
| SEC-05 | No MFA | Username + password only | P1 | E4 |
| SEC-06 | No SSO / SAML integration | No IdP integration | P1 | E4 |
| SEC-07 | No OWASP Top 10 audit | No evidence of security scan | P1 | E4 |
| SEC-08 | No dependency vulnerability audit | No `pip audit` / `npm audit` in CI | P1 | E4 |
| SEC-09 | No concurrent session limits | Unlimited simultaneous JWTs | P1 | E4 |
| SEC-10 | No JWT revocation list | Logout does not invalidate tokens server-side | P1 | E4 |
| SEC-11 | No field-level encryption for PII | User email stored plaintext | P2 | E4 |
| SEC-12 | Storage paths not namespaced by tenant | Shared directory structure | P1 | E4 |
| SEC-13 | No POPIA compliance documentation | No DPIA, no retention schedule | P1 | E5 (Governance) |
| SEC-14 | No AI output audit trail | AI conversations not immutably logged | P1 | E5 |
| SEC-15 | Session tokens not scoped to IP or device | Session fixation risk | P2 | E4 |

---

## 2. Observability Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| OBS-01 | No structured logging | `print()` and basic Python logging only | P0 | E6 (Ops) |
| OBS-02 | No metrics endpoint | No Prometheus `/metrics` | P1 | E6 |
| OBS-03 | No error tracking | No Sentry or equivalent | P1 | E6 |
| OBS-04 | No distributed tracing | No OpenTelemetry spans | P2 | E6 |
| OBS-05 | No uptime monitoring | No external health check monitor | P1 | E6 |
| OBS-06 | No log aggregation | No ELK/Loki stack | P2 | E6 |
| OBS-07 | No alerting | No PagerDuty, Opsgenie, or equivalent | P2 | E6 |
| OBS-08 | No AI cost tracking | Model API spend not instrumented | P2 | E6 |
| OBS-09 | No per-tenant usage metrics | No breakdown by institution | P2 | E6 |

---

## 3. Background Processing Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| BG-01 | No task queue | `FastAPI BackgroundTasks` only (in-process) | P1 | E1 (Autonomous Monitoring) |
| BG-02 | No scheduled job runner | No APScheduler, Celery Beat, or cron | P1 | E1 |
| BG-03 | Background tasks lost on restart | No persistence of queued work | P1 | E1 |
| BG-04 | No retry with backoff | Failed tasks silently dropped | P1 | E1 |
| BG-05 | No dead-letter queue | No capture of permanently failed jobs | P2 | E1 |
| BG-06 | No task status visibility | Users cannot see queue depth or wait time | P2 | E1 |

---

## 4. Analytics and Reporting Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| ANA-01 | No compliance trend charts | Entity counts only in dashboard | P1 | E3 (Analytics) |
| ANA-02 | No audit cycle comparison | No period-over-period analysis | P1 | E3 |
| ANA-03 | No heat map views | No faculty/dept compliance heat map | P1 | E3 |
| ANA-04 | No predictive risk scoring | No leading indicator analysis | P2 | E3 |
| ANA-05 | PDF export is placeholder | Endpoint returns placeholder response | P1 | E3 |
| ANA-06 | No DOCX export | JSON and Markdown only | P2 | E3 |
| ANA-07 | No XLSX export of raw data | CSV only | P2 | E3 |
| ANA-08 | No scheduled report delivery | No email or SFTP delivery of reports | P2 | E3 |
| ANA-09 | No executive summary dashboard | No institution-level one-page summary | P1 | E3 |
| ANA-10 | No comparative benchmarking | No inter-institution or CHE benchmarks | P3 | E3 |

---

## 5. Regulatory Knowledge Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| REG-01 | No OFFICIAL_VERIFIED CHE documents | Test fixtures only (28–196 vectors) | P0 | E2 (Regulatory) |
| REG-02 | No DHET regulatory framework indexed | Missing | P0 | E2 |
| REG-03 | No SAQA NQF standards indexed | Missing | P0 | E2 |
| REG-04 | No QCTO occupational qualifications | Missing | P1 | E2 |
| REG-05 | No ECSA engineering programme accreditation | Missing | P2 | E2 |
| REG-06 | No HPCSA health professions accreditation | Missing | P2 | E2 |
| REG-07 | No SACE educator accreditation | Missing | P2 | E2 |
| REG-08 | No institutional policy document indexing | No workflow to add per-institution policy | P1 | E2 |
| REG-09 | No regulatory document version management | SourceStatus exists; no change-tracking | P1 | E2 |
| REG-10 | No regulator citation confidence scoring | Citations provided without confidence score | P2 | E2 |

---

## 6. Workflow and Corrective Action Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| WF-01 | No structured CorrectiveAction model | Conversational only in AI Workspace | P1 | E1 |
| WF-02 | No due-date tracking on findings | No deadline enforcement | P1 | E1 |
| WF-03 | No assignee tracking on findings | ASSIGNED state exists; no user linkage | P1 | E1 |
| WF-04 | No reminder/notification on overdue items | In-app notifications exist; no automation | P1 | E1 |
| WF-05 | No corrective action plan template | No structured CAP document generator | P2 | E1 |
| WF-06 | No evidence-of-resolution workflow | No mechanism to confirm finding is closed | P1 | E1 |
| WF-07 | No escalation automation | ESCALATED state exists; no auto-trigger | P2 | E1 |
| WF-08 | Student experience not defined | Student role is placeholder | P3 | E7 (UX) |

---

## 7. Deployment and DevOps Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| DEP-01 | No environment separation | Single `backend/.env` for all environments | P0 | E6 |
| DEP-02 | No CI/CD pipeline | No GitHub Actions, no automated test/build | P1 | E6 |
| DEP-03 | No production Docker Compose | Only dev compose file exists | P0 | E6 |
| DEP-04 | No Kubernetes / container orchestration | Docker Compose only | P2 | E6 |
| DEP-05 | No automated database backup | Manual pg_dump only | P0 | E6 |
| DEP-06 | No automated Qdrant snapshot | Manual snapshot API only | P1 | E6 |
| DEP-07 | No rollback automation | Manual alembic downgrade only | P1 | E6 |
| DEP-08 | No staging environment | Local only | P1 | E6 |
| DEP-09 | No production TLS termination | HTTP on port 8000 | P0 | E6 |
| DEP-10 | No resource limits in Docker | No CPU/memory constraints | P1 | E6 |

---

## 8. Tenant Onboarding Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| ONB-01 | No tenant provisioning API | Manual seed scripts only | P0 | E7 |
| ONB-02 | No institution onboarding wizard | Admin CRUD exists; no guided flow | P1 | E7 |
| ONB-03 | No IKP auto-setup for new tenants | Manual reindex script only | P0 | E7 |
| ONB-04 | No institution branding configuration | No logo, theme, or colour per tenant | P2 | E7 |
| ONB-05 | No bulk user import | Manual registration only | P1 | E7 |
| ONB-06 | No tenant readiness checklist | No automated pre-go-live validation | P1 | E7 |
| ONB-07 | No SSO per-tenant configuration | Global auth only | P2 | E7 |

---

## 9. User Experience Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| UX-01 | No user onboarding tour | Direct access to workspace | P1 | E7 |
| UX-02 | No in-app help system | No contextual help or tooltips | P2 | E7 |
| UX-03 | No WCAG 2.1 AA audit | ARIA labels present; not audited | P1 | E7 |
| UX-04 | Module context not restored on reload | L-05 known limitation | P1 | E7 |
| UX-05 | No keyboard shortcut reference | No discoverability | P3 | E7 |
| UX-06 | No mobile-first audit | Responsive CSS present; not tested on device | P2 | E7 |
| UX-07 | No HOD/Dean dedicated dashboard | Generic views only | P2 | E7 |
| UX-08 | No faculty compliance heatmap | Not implemented | P1 | E3 |

---

## 10. AI Governance Gaps

| ID | Gap | Current State | Priority | Phase E Workstream |
|----|-----|--------------|----------|-------------------|
| AI-01 | No AI output audit log | AI responses not immutably logged | P1 | E5 |
| AI-02 | No hallucination incident tracking | No structured capture of AI errors | P1 | E5 |
| AI-03 | No model provider failover | Single provider dependency | P2 | E5 |
| AI-04 | No AI cost governance | No per-tenant AI cost cap | P2 | E5 |
| AI-05 | No AI response quality metric | No BLEU/ROUGE or manual evaluation protocol | P2 | E5 |
| AI-06 | No grounding coverage metric | % of responses with verified sources unknown | P1 | E5 |
| AI-07 | No user feedback on AI responses | No thumbs up/down on workspace responses | P2 | E5 |
| AI-08 | No context window monitoring | No alert when nearing token limit | P2 | E5 |

---

## Priority Summary

| Priority | Count | Meaning |
|----------|-------|---------|
| P0 | 18 | Pilot blocker — must be resolved before first live tenant |
| P1 | 42 | Commercial launch blocker — required for production |
| P2 | 26 | Competitive gap — expected in enterprise product |
| P3 | 5 | Future enhancement |

**Total gaps identified:** 91

---

## P0 Gap Consolidated List (Pilot Blockers)

1. SEC-01: Rate limiting
2. SEC-02: HTTPS enforcement
3. SEC-03: Secrets management
4. SEC-04: Virus scanning enabled
5. SEC-12: Storage path tenant namespacing
6. OBS-01: Structured logging
7. REG-01: CHE official documents indexed
8. REG-02: DHET regulatory framework indexed
9. REG-03: SAQA NQF standards indexed
10. DEP-01: Environment separation
11. DEP-03: Production Docker Compose
12. DEP-05: Automated database backup
13. DEP-09: Production TLS termination
14. ONB-01: Tenant provisioning API
15. ONB-03: IKP auto-setup for new tenants
16. BG-01: Task queue (required for autonomous monitoring)
17. BG-02: Scheduled job runner
18. BG-03: Background task persistence

---

## Referenced Documents

- [AQAA_PHASE_D_CAPABILITY_INVENTORY.md](AQAA_PHASE_D_CAPABILITY_INVENTORY.md)
- [AQAA_PHASE_D_KNOWN_LIMITATIONS.md](../releases/phase-d/AQAA_PHASE_D_KNOWN_LIMITATIONS.md)
- Phase E workstream breakdown: [AQAA_PHASE_E_VISION_AND_SCOPE.md](AQAA_PHASE_E_VISION_AND_SCOPE.md)
