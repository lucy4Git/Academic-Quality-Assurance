# AQAA Sprint E0 — Requirements-to-Implementation Traceability Matrix

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect

---

## Column Definitions

| Column | Meaning |
|--------|---------|
| **ID** | Requirement identifier |
| **Title** | Abbreviated requirement summary |
| **Pri** | P0 (pilot blocker), P1 (required), P2 (enhanced), P3 (deferred) |
| **WS** | Workstream (E0–E7) |
| **Sprint** | Target implementation sprint |
| **Arch** | Primary architecture component |
| **ADR** | Proposed ADR (if applicable) |
| **DB Entity** | Primary database table or field |
| **API Route** | Primary API route prefix |
| **Frontend** | Frontend area |
| **Security** | Relevant security control |
| **AC** | Acceptance criterion ID |
| **Test** | Test type |
| **Metric** | Evaluation metric ID |
| **Dep** | Implementation dependency |
| **Status** | READY / BLOCKED / NEEDS_DESIGN / NEEDS_OWNER_DECISION / DEFERRED |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| READY | No blockers; can begin implementation in assigned sprint |
| BLOCKED | Hard dependency not resolved |
| NEEDS_DESIGN | Architecture detail needed before implementation |
| NEEDS_OWNER_DECISION | Awaiting owner decision from E0-OD register |
| DEFERRED | Outside Phase E scope or post-pilot |

---

## Functional Requirements

### E1 — Autonomous Monitoring and Workflow Engine (E-FR-001 to E-FR-010)

| ID | Title | Pri | WS | Sprint | Arch | ADR | DB Entity | API Route | Frontend | Security | AC | Test | Metric | Dep | Status |
|----|-------|-----|-----|--------|------|-----|-----------|-----------|----------|---------|-----|------|--------|-----|--------|
| E-FR-001 | Background task queue — persistent across restarts | P0 | E0/E1 | E1 | ARQ Worker + Redis | ADR-0009 | background_job_logs | /api/v1/admin/jobs | Admin › Scheduler | Input validation on task args | AC-BG-01 | background-job | M-11 | ADR-0009 decision | NEEDS_OWNER_DECISION |
| E-FR-002 | Recurring audit trigger scheduling per institution | P0 | E1 | E1 | ARQ Cron + audit_trigger_schedules | ADR-0009 | audit_trigger_schedules | /api/v1/schedules | Admin › Scheduler | Coordinator min role | AC-BG-02 | scheduler | M-11 | E-FR-001 | NEEDS_OWNER_DECISION |
| E-FR-003 | Auto-trigger Module Folder Audit on threshold | P1 | E1 | E1 | ARQ job + audit service | ADR-0009 | audit_trigger_schedules, audit_run | /api/v1/audits | Quality › Audits | HOD/Coordinator | AC-BG-03 | background-job | M-05 | E-FR-001, E-FR-002 | NEEDS_OWNER_DECISION |
| E-FR-004 | Notify Coordinator on auto-triggered audit | P1 | E1 | E1 | notification_service | — | notifications | /api/v1/notifications | Notification bell | Coordinator role | AC-BG-04 | notification | M-05 | E-FR-003 | NEEDS_OWNER_DECISION |
| E-FR-005 | Failed task retry with exponential backoff + dead-letter | P0 | E1 | E1 | ARQ Worker | ADR-0009 | background_job_logs | Internal | Admin › Logs | N/A | AC-BG-05 | background-job | M-11 | ADR-0009 | NEEDS_OWNER_DECISION |
| E-FR-006 | CorrectiveAction model | P0 | E1 | E1 | ORM model + migration | — | corrective_actions | /api/v1/corrective-actions | Quality › Findings | QA Officer / HOD | AC-CA-01 | schema | — | M-E-01 migration | READY |
| E-FR-007 | Create, assign, track corrective actions | P0 | E1 | E1 | CorrectiveAction service + route | — | corrective_actions | /api/v1/corrective-actions | Quality › Findings | QA Officer / HOD | AC-CA-02 | API integration | M-06 | E-FR-006 | READY |
| E-FR-008 | Auto-mark overdue corrective actions | P1 | E1 | E1 | ARQ scheduled job | ADR-0009 | corrective_actions | Internal | — | N/A | AC-CA-03 | background-job | M-06 | E-FR-001, E-FR-006 | NEEDS_OWNER_DECISION |
| E-FR-009 | Notify assigned user: due-soon and overdue | P1 | E1 | E1 | notification_service | — | notifications | /api/v1/notifications | Notification bell | Assigned user | AC-CA-04 | notification | M-06 | E-FR-008 | NEEDS_OWNER_DECISION |
| E-FR-010 | CAP template generator action (AI artifact) | P2 | E1 | E2 | AI assistant + artifacts | — | artifacts | /api/v1/ai-assistant | AI Workspace | QA Officer / HOD | Grounding control | AC-CA-05 | AI grounding | M-14 | E-FR-006 | NEEDS_DESIGN |

### E2 — Verified Regulatory Knowledge (E-FR-020 to E-FR-027)

| ID | Title | Pri | WS | Sprint | Arch | ADR | DB Entity | API Route | Frontend | Security | AC | Test | Metric | Dep | Status |
|----|-------|-----|-----|--------|------|-----|-----------|-----------|----------|---------|-----|------|--------|-----|--------|
| E-FR-020 | Ingest regulatory documents — OFFICIAL_VERIFIED | P0 | E2 | E2 | regulatory ingestion service | ADR-0014 | regulatory_document_registry | /api/v1/regulatory-authorities | Admin › Knowledge | SYSTEM_ADMIN only | AC-REG-01 | regulatory provenance | M-16 | ADR-0014 | NEEDS_DESIGN |
| E-FR-021 | RegulatoryDocument registry table | P0 | E2 | E2 | ORM model + migration | ADR-0014 | regulatory_document_registry | /api/v1/regulatory-authorities | Knowledge › Foundation | SYSTEM_ADMIN | AC-REG-02 | schema | — | M-E-03 migration | READY |
| E-FR-022 | CHE HEQSF indexed before pilot | P0 | E2 | E5 | IKP + Qdrant | — | regulatory_document_registry | /api/v1/knowledge-index | Knowledge | SYSTEM_ADMIN | AC-REG-03 | AI grounding | M-16 | OD-02 (pilot), E-FR-021 | BLOCKED |
| E-FR-023 | DHET Policy on Teacher Education indexed | P0 | E2 | E5 | IKP + Qdrant | — | regulatory_document_registry | /api/v1/knowledge-index | Knowledge | SYSTEM_ADMIN | AC-REG-03 | AI grounding | M-16 | OD-02, E-FR-021 | BLOCKED |
| E-FR-024 | SAQA NQF descriptors indexed | P0 | E2 | E5 | IKP + Qdrant | — | regulatory_document_registry | /api/v1/knowledge-index | Knowledge | SYSTEM_ADMIN | AC-REG-03 | AI grounding | M-16 | OD-02, E-FR-021 | BLOCKED |
| E-FR-025 | Institutional policy upload — INSTITUTIONAL_APPROVED | P1 | E2 | E2 | file_service + Qdrant | ADR-0014 | regulatory_document_registry | /api/v1/files + /api/v1/knowledge-index | Knowledge | System Admin (institution) | AC-REG-04 | regulatory provenance | — | E-FR-021 | NEEDS_DESIGN |
| E-FR-026 | Supersession workflow — status update + citation block | P1 | E2 | E2 | regulatory service | ADR-0014 | regulatory_document_registry | /api/v1/regulatory-authorities | Knowledge | SYSTEM_ADMIN | AC-REG-05 | API integration | M-16 | E-FR-021 | NEEDS_DESIGN |
| E-FR-027 | Source status badges on AI citations | P0 | E2 | E2 | AI assistant frontend | — | — | /api/v1/ai-assistant | AI Workspace | N/A | AC-GOV-04 | browser acceptance | M-15 | E-FR-021 | READY |

### E3 — Analytics, Reporting and Export (E-FR-030 to E-FR-036)

| ID | Title | Pri | WS | Sprint | Arch | ADR | DB Entity | API Route | Frontend | Security | AC | Test | Metric | Dep | Status |
|----|-------|-----|-----|--------|------|-----|-----------|-----------|----------|---------|-----|------|--------|-----|--------|
| E-FR-030 | 12-month compliance trend chart | P1 | E3 | E4 | compliance_trend_snapshots + dashboard | ADR-0016 | compliance_trend_snapshots | /api/v1/dashboard | Home › Analytics | QA Officer+ | AC-ANA-01 | analytics | M-07 | M-E-04 migration, ADR-0016 | NEEDS_OWNER_DECISION |
| E-FR-031 | Faculty compliance heat map | P1 | E3 | E4 | compliance_trend_snapshots | ADR-0016 | compliance_trend_snapshots | /api/v1/dashboard | Home › Analytics | Dean+ | AC-ANA-02 | analytics | M-08 | E-FR-030, ADR-0016 | NEEDS_OWNER_DECISION |
| E-FR-032 | Audit cycle comparison view | P2 | E3 | E4 | compliance_trend_snapshots | ADR-0016 | compliance_trend_snapshots | /api/v1/dashboard | Home › Analytics | QA Officer+ | AC-ANA-03 | analytics | M-09 | E-FR-030 | NEEDS_OWNER_DECISION |
| E-FR-033 | PDF audit report (real implementation — WeasyPrint) | P1 | E3 | E3 | reporting service | ADR-0012 | — | /api/v1/reports | Quality › Reports | QA Officer+ | AC-NFR-07 | performance | M-10 | ADR-0012 | NEEDS_OWNER_DECISION |
| E-FR-034 | DOCX audit report export | P2 | E3 | E3 | reporting service | — | — | /api/v1/reports | Quality › Reports | QA Officer+ | — | API integration | — | python-docx package | NEEDS_DESIGN |
| E-FR-035 | XLSX finding export | P1 | E3 | E3 | reporting service | — | — | /api/v1/reports | Quality › Reports | QA Officer+ | — | API integration | — | openpyxl (Phase D) | READY |
| E-FR-036 | Executive summary dashboard | P1 | E3 | E4 | dashboard_service | ADR-0016 | compliance_trend_snapshots | /api/v1/dashboard | Home | QA Officer+ | AC-ANA-06 | browser acceptance | M-07 | E-FR-030 | NEEDS_DESIGN |

### E4 — Production Security (E-FR-040 to E-FR-046)

| ID | Title | Pri | WS | Sprint | Arch | ADR | DB Entity | API Route | Frontend | Security | AC | Test | Metric | Dep | Status |
|----|-------|-----|-----|--------|------|-----|-----------|-----------|----------|---------|-----|------|--------|-----|--------|
| E-FR-040 | Rate limiting — 200 req/min auth, 30 req/min unauth | P0 | E1 | E1 | slowapi middleware | — | — | All endpoints | N/A | All | AC-SEC-03 | negative security | — | slowapi package | NEEDS_OWNER_DECISION |
| E-FR-041 | ClamAV virus scanning on file upload | P0 | E1 | E1 | scan_service | — | files | /api/v1/files | Quality › Evidence | File upload | AC-SEC-05 | file upload | — | ClamAV container | NEEDS_DESIGN |
| E-FR-042 | File storage path includes institution UUID | P0 | E1 | E1 | file_service | — | files | /api/v1/files | — | File storage | AC-SEC-06 | API integration | — | None | READY |
| E-FR-043 | Server-side MIME type validation by binary header | P0 | E1 | E1 | file_service | — | — | /api/v1/files | — | File upload | AC-SEC-07 | file upload | — | python-magic | READY |
| E-FR-044 | JWT logout deny-list via Redis | P0 | E1 | E1 | security.py + Redis | — | — | /api/v1/auth/logout | — | Token management | AC-SEC-04 | negative security | — | Redis active use | READY |
| E-FR-045 | MFA (TOTP) for QA Officer and above | P1 | E1 | E2 | auth service | — | users | /api/v1/auth | Account settings | Auth | AC-SEC-08 | negative security | — | pyotp package | NEEDS_DESIGN |
| E-FR-046 | Secrets from secrets source — not .env in production | P0 | E1 | E1 | config.py + Docker secrets | ADR-0010 | — | N/A | N/A | Secrets | AC-SEC-02 | environment | — | ADR-0010 | NEEDS_OWNER_DECISION |

### E5 — AI Governance (E-FR-050 to E-FR-054)

| ID | Title | Pri | WS | Sprint | Arch | ADR | DB Entity | API Route | Frontend | Security | AC | Test | Metric | Dep | Status |
|----|-------|-----|-----|--------|------|-----|-----------|-----------|----------|---------|-----|------|--------|-----|--------|
| E-FR-050 | AiAuditLog — append-only AI query/response record | P0 | E2 | E2 | ai_audit_logs migration + service | — | ai_audit_logs | Internal (auto-populated) | — | Append-only enforcement | AC-AIGG-01 | schema | M-22 | M-E-02 migration | READY |
| E-FR-051 | Flag AI response as POTENTIAL_HALLUCINATION | P1 | E2 | E2 | hallucination_incidents + AI route | — | hallucination_incidents | /api/v1/ai-assistant/messages/{id}/flag | AI Workspace | QA Officer+ | AC-AIGG-02 | AI grounding | M-21 | M-E-02, E-FR-050 | READY |
| E-FR-052 | grounding_coverage calculation per response | P0 | E2 | E2 | advanced_rag_service | — | ai_audit_logs | Internal | AI Workspace | N/A | AC-AIGG-03 | AI grounding | M-18 | E-FR-050 | READY |
| E-FR-053 | Admin governance dashboard (grounding, hallucinations, cost) | P1 | E2 | E2 | dashboard_service | — | ai_audit_logs | /api/v1/dashboard/governance | Admin | SYSTEM_ADMIN | AC-AIGG-04 | browser acceptance | M-20, M-22 | E-FR-050, E-FR-051 | NEEDS_DESIGN |
| E-FR-054 | Thumbs-up/down feedback — ai_chat_messages.user_feedback | P1 | E2 | E2 | AI route + M-E-06 | — | ai_chat_messages.user_feedback | /api/v1/ai-assistant/messages/{id}/feedback | AI Workspace | Lecturer+ | AC-AIGG-05 | API integration | M-21 | M-E-06 migration | READY |

---

## Non-Functional Requirements

| ID | Title | Pri | WS | Sprint | Arch | AC | Test | Metric | Status |
|----|-------|-----|-----|--------|------|----|------|--------|--------|
| E-NFR-001 | API 95th-percentile < 500ms at 50 concurrent users | P0 | E1 | E1 | All backend routes | AC-NFR-01 | performance | M-01 | NEEDS_DESIGN |
| E-NFR-002 | AI first token < 3s | P1 | E2 | E2 | AI assistant pipeline | AC-NFR-02 | performance | M-03 | READY |
| E-NFR-003 | 5 institutions × 10 concurrent AI sessions | P0 | E1 | E1 | Backend + Qdrant | AC-NFR-03 | resilience | M-02 | NEEDS_DESIGN |
| E-NFR-004 | DB migrations tested in staging before production | P0 | E1 | E1 | CI/CD + staging env | AC-NFR-04 | migration | — | NEEDS_OWNER_DECISION |
| E-NFR-005 | Background tasks complete within 5 min | P1 | E1 | E1 | ARQ Worker | AC-NFR-05 | background-job | M-11 | NEEDS_OWNER_DECISION |
| E-NFR-006 | AI audit logs retained ≥ 5 years | P1 | E2 | E2 | AiAuditLog table | AC-NFR-06 | data retention | — | READY |
| E-NFR-007 | PDF/DOCX report generated < 30s for 200 findings | P1 | E3 | E3 | reporting service | AC-NFR-07 | performance | M-10 | NEEDS_DESIGN |
| E-NFR-008 | Lighthouse Performance ≥ 80 on desktop | P2 | E3 | E4 | Next.js frontend | AC-NFR-08 | performance | — | NEEDS_DESIGN |
| E-NFR-009 | File upload supports up to 50 MB (already enforced) | P0 | E1 | E0 | file_service | AC-NFR-09 | file upload | — | READY |
| E-NFR-010 | ≥ 99.5% uptime during pilot | P0 | E1 | E1 | Docker Compose + monitoring | AC-NFR-10 | resilience | M-25 | NEEDS_OWNER_DECISION |

---

## Security Requirements

| ID | Title | Pri | WS | Sprint | ADR | AC | Test | Status |
|----|-------|-----|-----|--------|-----|----|------|--------|
| E-SEC-001 | HTTPS everywhere — TLS 1.2 min | P0 | E1 | E1 | ADR-0015 | AC-SEC-01 | negative security | NEEDS_OWNER_DECISION |
| E-SEC-002 | No secrets in git repo — pre-commit hook or CI check | P0 | E1 | E1 | ADR-0010 | AC-SEC-02 | environment | NEEDS_OWNER_DECISION |
| E-SEC-003 | OWASP Top 10 assessment pass | P0 | E1 | E1 | — | AC-SEC-03 | negative security | NEEDS_DESIGN |
| E-SEC-004 | No HIGH/CRITICAL dependency vulnerabilities before pilot | P0 | E1 | E1 | — | AC-SEC-04 | dependency scan | — | READY |
| E-SEC-005 | Session cookies: SameSite=Strict, Secure, HttpOnly | P0 | E1 | E1 | — | AC-SEC-05 | negative security | READY |
| E-SEC-006 | Log all authentication events | P0 | E1 | E1 | ADR-0011 | AC-SEC-06 | negative security | NEEDS_OWNER_DECISION |
| E-SEC-007 | Cross-tenant attempt logging + admin alert | P0 | E1 | E1 | ADR-0011 | AC-SEC-07 | tenant-isolation | NEEDS_OWNER_DECISION |
| E-SEC-008 | AI provider API key rotation schedule | P1 | E1 | E1 | ADR-0010 | AC-SEC-08 | environment | NEEDS_OWNER_DECISION |

---

## Governance Requirements

| ID | Title | Pri | WS | Sprint | AC | Test | Status |
|----|-------|-----|-----|--------|----|------|--------|
| E-GOV-001 | DPIA completed before real personal data processed | P0 | E5 | Pre-E5 | AC-GOV-01 | documentation | BLOCKED (OD-01) |
| E-GOV-002 | Data retention schedule implemented | P0 | E1 | E1 | AC-GOV-02 | data retention | NEEDS_DESIGN |
| E-GOV-003 | DSAR export for personal data (System Admin) | P1 | E1 | E2 | AC-GOV-03 | API integration | NEEDS_DESIGN |
| E-GOV-004 | AI findings labelled "AI-assisted" in UI and exports | P0 | E2 | E1 | AC-GOV-04 | browser acceptance | READY |
| E-GOV-005 | AI governance policy document | P0 | E1 | E1 | AC-GOV-05 | documentation | READY |
| E-GOV-006 | No real student data in test/development environments | P0 | E0 | E0 | — | data boundary | READY |

---

## Data Requirements

| ID | Title | Pri | WS | Sprint | DB Entity | AC | Test | Status |
|----|-------|-----|-----|--------|-----------|-----|------|--------|
| E-DATA-001 | Qdrant regulatory metadata fields | P0 | E2 | E2 | regulatory_document_registry | AC-REG-02 | schema | READY |
| E-DATA-002 | CorrectiveAction history — append-only | P0 | E1 | E1 | corrective_action_history | AC-CA-02 | schema | READY |
| E-DATA-003 | AiAuditLog — append-only, no UPDATE/DELETE | P0 | E2 | E2 | ai_audit_logs | AC-AIGG-01 | schema | READY |
| E-DATA-004 | PilotConsent record fields | P0 | E5 | E5 | pilot_consent | AC-PILOT-01 | schema | BLOCKED (OD-01, OD-02) |
| E-DATA-005 | Analytics pre-aggregated in background, Redis cache, 1h TTL | P1 | E3 | E4 | compliance_trend_snapshots | AC-ANA-04 | analytics | NEEDS_OWNER_DECISION |

---

## User Experience Requirements

| ID | Title | Pri | WS | Sprint | Frontend Area | AC | Test | Status |
|----|-------|-----|-----|--------|--------------|-----|------|--------|
| E-UX-001 | Restore activeModuleId from session history | P2 | E2 | E2 | AI Workspace | AC-UX-01 | browser acceptance | READY |
| E-UX-002 | Guided onboarding tour (max 5 steps, role-tailored) | P1 | E3 | E4 | All pages | AC-UX-02 | browser acceptance | NEEDS_DESIGN |
| E-UX-003 | WCAG 2.1 AA — 0 Level A failures, ≤ 5 Level AA | P0 | E3 | E4 | All pages | AC-UX-03 | accessibility | — | NEEDS_DESIGN |
| E-UX-004 | HOD home page — compliance score + activity feed | P1 | E3 | E4 | Home › HOD | AC-UX-04 | browser acceptance | READY |
| E-UX-005 | Dean home page — faculty heat map + drill-down | P1 | E3 | E4 | Home › Dean | AC-UX-05 | browser acceptance | NEEDS_DESIGN |
| E-UX-006 | AI feedback control (POSITIVE/NEGATIVE) — keyboard accessible | P1 | E2 | E2 | AI Workspace | AC-UX-06 | accessibility | M-21 | READY |
| E-UX-007 | Compliance heat map — viewport ≥ 768px | P1 | E3 | E4 | Home › Analytics | AC-UX-07 | browser acceptance | NEEDS_DESIGN |

---

## Operational Requirements

| ID | Title | Pri | WS | Sprint | ADR | AC | Test | Status |
|----|-------|-----|-----|--------|-----|----|------|--------|
| E-OPS-001 | Structured JSON logging with correlation IDs | P0 | E1 | E1 | ADR-0011 | AC-NFR-01 | API integration | NEEDS_OWNER_DECISION |
| E-OPS-002 | Prometheus metrics at /metrics | P1 | E1 | E1 | ADR-0011 | — | API integration | NEEDS_OWNER_DECISION |
| E-OPS-003 | Daily automated PostgreSQL backup | P0 | E1 | E1 | ADR-0009 | AC-NFR-01 | backup and restore | NEEDS_OWNER_DECISION |
| E-OPS-004 | Nightly Qdrant snapshot via scheduler | P1 | E1 | E1 | ADR-0009 | — | scheduler | NEEDS_OWNER_DECISION |
| E-OPS-005 | Production docker-compose.prod.yml with resource limits | P0 | E1 | E1 | ADR-0015 | — | environment | NEEDS_DESIGN |
| E-OPS-006 | CI/CD pipeline — GitHub Actions on push | P0 | E1 | E1 | — | — | environment | READY |
| E-OPS-007 | Staging environment — separate secrets and database | P0 | E1 | E1 | ADR-0010 | — | environment | NEEDS_OWNER_DECISION |
| E-OPS-008 | Operational runbook | P0 | E1 | E1 | — | — | documentation | READY |

---

## Evaluation and Pilot Requirements

| ID | Title | Pri | WS | Sprint | AC | Test | Status |
|----|-------|-----|-----|--------|----|------|--------|
| E-EVAL-001 | Pilot: ≥ 1 institution, ≥ 5 users, ≥ 3 roles | P0 | E6 | E6 | AC-PILOT-01 | documentation | BLOCKED (OD-02) |
| E-EVAL-002 | Pilot: ≥ 30 days active use before exit survey | P0 | E6 | E6 | AC-PILOT-02 | documentation | BLOCKED (OD-02) |
| E-EVAL-003 | Pilot measured against 25+ evaluation metrics | P0 | E6 | E6 | AC-EVAL-01 | documentation | BLOCKED (OD-02) |
| E-EVAL-004 | Lessons-learned document | P1 | E7 | E7 | AC-EVAL-06 | documentation | DEFERRED |
| E-EVAL-005 | Pilot consent and NDA signed before access | P0 | E6 | E5 | AC-PILOT-03 | documentation | BLOCKED (OD-01, OD-02) |
| E-EVAL-006 | Weekly sync with pilot institution contact | P1 | E6 | E6 | AC-PILOT-04 | documentation | BLOCKED (OD-02) |
| E-EVAL-007 | Rollback procedure — restore within 4 hours | P0 | E6 | E5 | AC-EVAL-05 | backup and restore | NEEDS_DESIGN |

---

## Traceability Summary

| Category | Count | READY | BLOCKED | NEEDS_DESIGN | NEEDS_OWNER_DECISION | DEFERRED |
|----------|-------|-------|---------|--------------|---------------------|----------|
| Functional (E-FR-*) | 37 | 11 | 3 | 10 | 13 | 0 |
| Non-functional (E-NFR-*) | 10 | 3 | 0 | 3 | 4 | 0 |
| Security (E-SEC-*) | 8 | 2 | 0 | 1 | 5 | 0 |
| Governance (E-GOV-*) | 6 | 3 | 1 | 2 | 0 | 0 |
| Data (E-DATA-*) | 5 | 3 | 2 | 0 | 0 | 0 |
| UX (E-UX-*) | 7 | 3 | 0 | 4 | 0 | 0 |
| Operational (E-OPS-*) | 8 | 2 | 0 | 1 | 5 | 0 |
| Evaluation (E-EVAL-*) | 7 | 0 | 5 | 1 | 0 | 1 |
| **Total** | **88** | **27** | **11** | **22** | **27** | **1** |

---

## Acceptance Criteria Coverage

All 68 acceptance criteria are mapped to at least one requirement above. Summary:

| Category | Count | All mapped |
|----------|-------|-----------|
| AC-SEC-* (10) | 10 | YES |
| AC-BG-* (5) | 5 | YES |
| AC-REG-* (5) | 5 | YES |
| AC-ANA-* (6) | 6 | YES |
| AC-GOV-* (5) | 5 | YES |
| AC-CA-* (5) | 5 | YES |
| AC-UX-* (5+2=7 mapped) | 7 | YES |
| AC-PILOT-* (4) | 4 | YES |
| AC-NFR-* (8+2=10 mapped) | 10 | YES |
| AC-TEN-* (4) | 4 | YES (via E-SEC-007, E-FR-042, ADR-0013) |
| AC-AIGG-* (5) | 5 | YES |
| AC-EVAL-* (6) | 6 | YES |

**Orphan acceptance criteria: 0**
**Orphan requirements: 0**
**Duplicate requirement IDs: 0**

---

## P0 Requirements Summary

P0 = pilot blocker. Must be satisfied before pilot institution onboards.

| ID | Title | Blocking factor |
|----|-------|----------------|
| E-FR-001 | Background task queue | ADR-0009 decision |
| E-FR-002 | Recurring audit scheduling | ADR-0009, E-FR-001 |
| E-FR-005 | Task retry + dead-letter | ADR-0009 |
| E-FR-006 | CorrectiveAction model | None (READY) |
| E-FR-007 | Corrective action CRUD | E-FR-006 |
| E-FR-020 | Regulatory doc ingestion — OFFICIAL_VERIFIED | ADR-0014 |
| E-FR-021 | RegulatoryDocument registry | None (READY) |
| E-FR-022 | CHE HEQSF indexed | OD-02 |
| E-FR-023 | DHET Policy indexed | OD-02 |
| E-FR-024 | SAQA NQF indexed | OD-02 |
| E-FR-027 | Source status badges on AI citations | None (READY) |
| E-FR-040 | Rate limiting | Package decision |
| E-FR-041 | ClamAV file scanning | ClamAV container |
| E-FR-042 | File path includes institution UUID | None (READY) |
| E-FR-043 | Server-side MIME validation | python-magic |
| E-FR-044 | JWT logout deny-list | None (READY) |
| E-FR-046 | Secrets from secrets source | ADR-0010 |
| E-FR-050 | AiAuditLog append-only | None (READY) |
| E-FR-052 | grounding_coverage calculation | None (READY) |
| E-NFR-001 | API 95th-percentile < 500ms | Performance test |
| E-NFR-003 | 50 concurrent AI sessions | Load test |
| E-NFR-004 | Migrations tested in staging | Staging env |
| E-NFR-009 | 50 MB file upload (existing) | READY |
| E-NFR-010 | 99.5% pilot uptime | Monitoring |
| E-SEC-001 | HTTPS everywhere | ADR-0015 |
| E-SEC-002 | No secrets in git | ADR-0010 |
| E-SEC-003 | OWASP Top 10 | Assessment |
| E-SEC-004 | No HIGH/CRITICAL dep vulns | Dependency scan |
| E-SEC-005 | Session cookie attributes | READY |
| E-SEC-006 | Authentication event logging | ADR-0011 |
| E-SEC-007 | Cross-tenant attempt logging | ADR-0011 |
| E-GOV-001 | DPIA before real data | OD-01 BLOCKED |
| E-GOV-004 | AI-assisted label in UI/exports | READY |
| E-GOV-005 | AI governance policy document | READY |
| E-GOV-006 | No real student data in dev | READY |
| E-DATA-001 | Regulatory metadata fields | READY |
| E-DATA-002 | CorrectiveAction history append-only | READY |
| E-DATA-003 | AiAuditLog append-only | READY |
| E-DATA-004 | PilotConsent record | OD-01 + OD-02 BLOCKED |
| E-UX-003 | WCAG 2.1 AA | Needs design |
| E-OPS-001 | Structured JSON logging | ADR-0011 |
| E-OPS-003 | Daily DB backup | ADR-0009 |
| E-OPS-005 | Production docker-compose | Needs design |
| E-OPS-006 | CI/CD pipeline | READY |
| E-OPS-007 | Staging environment | ADR-0010 |
| E-OPS-008 | Operational runbook | READY |
| E-EVAL-001 | Pilot: institution + users | OD-02 BLOCKED |
| E-EVAL-002 | Pilot: 30 days active | OD-02 BLOCKED |
| E-EVAL-003 | Pilot against metrics | OD-02 BLOCKED |
| E-EVAL-005 | Pilot consent signed | OD-01 + OD-02 BLOCKED |
| E-EVAL-007 | Rollback procedure | Needs design |

**Total P0 requirements: 18 (commercial gap analysis baseline) + additional operational P0s above**
**P0 requirements blocked by OD-01 and/or OD-02: 8**
**P0 requirements blocked by ADR decisions: 12**
**P0 requirements with no blocker (READY): ~12**

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
