# AQAA Phase E — Requirements Specification

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

> Requirement IDs follow the scheme `E-{type}-{NNN}`.
> Types: **FR** (functional), **NFR** (non-functional), **SEC** (security), **GOV** (governance), **DATA** (data), **UX** (user experience), **OPS** (operational), **EVAL** (evaluation/pilot).

---

## Functional Requirements

### E1 — Autonomous Monitoring and Workflow Engine

**E-FR-001** The system shall provide a background task queue (ARQ or Celery) that persists task state across backend restarts.

**E-FR-002** The system shall support scheduling recurring audit triggers per institution, with configurable frequency (daily, weekly, per-programme).

**E-FR-003** The system shall automatically trigger Module Folder Audits for modules that have not been audited within a configurable threshold period.

**E-FR-004** The system shall send an in-app notification to the Programme Coordinator when a module audit is automatically triggered.

**E-FR-005** Failed background tasks shall be retried with exponential backoff (3 retries, 60/300/900 second intervals) before being moved to a dead-letter record.

**E-FR-006** The system shall provide a `CorrectiveAction` model with: `id`, `finding_id`, `assigned_to` (user), `due_date`, `status` (OPEN/IN_PROGRESS/OVERDUE/CLOSED), `description`, `evidence_of_resolution`, `created_at`, `updated_at`.

**E-FR-007** A QA Officer or HOD shall be able to create, assign, and track corrective actions against a finding through the AI Workspace or a dedicated corrective action panel.

**E-FR-008** The system shall automatically mark a corrective action as OVERDUE when its `due_date` passes without transition to CLOSED.

**E-FR-009** The system shall send an in-app notification to the assigned user when a corrective action is approaching its due date (3 days prior) and when it becomes overdue.

**E-FR-010** The AI Workspace shall provide a CAP (Corrective Action Plan) template generator action that drafts a structured corrective action plan document as an artifact, referencing the finding details and applicable regulatory clauses.

### E2 — Verified Regulatory Knowledge

**E-FR-020** The system shall support ingestion of regulatory documents into Qdrant with `source_status = OFFICIAL_VERIFIED`, requiring explicit operator authorisation per document.

**E-FR-021** The system shall maintain a `RegulatoryDocument` registry tracking: document title, issuing body, version, effective date, source URL, `source_status`, ingestion date, ingested_by, point_count.

**E-FR-022** The CHE HEQSF standards (minimum Level 5–10 descriptor set) shall be indexed as `OFFICIAL_VERIFIED` before the first pilot institution is onboarded.

**E-FR-023** The DHET Policy on the Minimum Requirements for Teacher Education Qualifications (latest version) shall be indexed as `OFFICIAL_VERIFIED`.

**E-FR-024** SAQA NQF level descriptors shall be indexed as `OFFICIAL_VERIFIED`.

**E-FR-025** Institutions shall be able to upload their own policy documents via the admin panel; these shall be indexed with `source_status = INSTITUTIONAL_APPROVED` and scoped to that institution's Qdrant namespace.

**E-FR-026** When a regulatory document is superseded, the system shall update its `source_status` to `SUPERSEDED` and prevent new citations from linking to it without operator confirmation.

**E-FR-027** The AI Workspace shall display source status badges (`OFFICIAL_VERIFIED`, `INSTITUTIONAL_APPROVED`, etc.) on every regulatory citation.

### E3 — Analytics, Reporting and Export

**E-FR-030** The dashboard shall provide a 12-month rolling compliance trend chart at institution, faculty, department, and programme levels.

**E-FR-031** The dashboard shall provide a compliance heat map at faculty level, using a colour scale from red (critical non-compliance) to green (fully compliant).

**E-FR-032** The dashboard shall support audit cycle comparison: selecting two date ranges and rendering a side-by-side compliance score comparison.

**E-FR-033** The reporting service shall produce a PDF audit report using a real document generation library (WeasyPrint or ReportLab), replacing the current placeholder. The report shall include: cover page, executive summary, findings table, evidence matrix, regulatory citation list.

**E-FR-034** The reporting service shall export audit reports in DOCX format using `python-docx`.

**E-FR-035** The reporting service shall export finding data in XLSX format using `openpyxl` (already available), including: finding ID, title, severity, type, status, assigned programme, assigned module, created date, resolved date.

**E-FR-036** An institution-level executive summary dashboard page shall provide: total audit count, finding severity breakdown (CRITICAL/HIGH/MEDIUM/LOW), compliance score trend, recent unresolved CRITICAL findings.

### E4 — Production Security

**E-FR-040** All API endpoints shall be protected by rate limiting: authenticated endpoints at 200 req/min per user; unauthenticated endpoints at 30 req/min per IP.

**E-FR-041** File uploads shall be scanned by ClamAV before transitioning from `scanning` to `ready` state. `VIRUS_SCAN_ENABLED` shall default to `True` in production configuration.

**E-FR-042** All uploaded files shall be stored at paths that include the institution UUID: `uploads/{institution_id}/{category}/{file_id}`.

**E-FR-043** The backend shall validate file MIME type server-side by inspecting the binary header, not relying on the client-supplied content-type.

**E-FR-044** JWT logout shall add the token `jti` to a Redis deny-list, invalidating the token immediately. The deny-list entry shall expire when the token would naturally expire.

**E-FR-045** MFA (TOTP) shall be enforced for `QUALITY_ASSURANCE_OFFICER` role and above. Users below that threshold may optionally enable MFA.

**E-FR-046** Application secrets (`SECRET_KEY`, database credentials, provider API keys) shall be loaded from a configurable secrets source (environment variable referencing a secrets file, or a mounted secrets volume) — not stored in the `.env` file in production.

### E5 — AI Governance

**E-FR-050** Every AI Workspace query and response shall be recorded in an append-only `AiAuditLog` table: `session_id`, `message_id`, `query_hash`, `response_hash`, `sources_cited[]`, `grounding_coverage` (float 0–1), `model_provider`, `model_name`, `tokens_prompt`, `tokens_completion`, `created_at`.

**E-FR-051** A QA Officer shall be able to flag an AI response as `POTENTIAL_HALLUCINATION`, which creates a `HallucinationIncident` record referencing the message and captures the reason text.

**E-FR-052** The system shall calculate `grounding_coverage` per AI response as the ratio of cited sources with `source_status IN (OFFICIAL_VERIFIED, INSTITUTIONAL_APPROVED)` to total sources cited. If no sources are cited, `grounding_coverage = 0`.

**E-FR-053** A System Administrator shall have access to a governance dashboard showing: per-institution `grounding_coverage` rolling average, hallucination incident count, AI cost (tokens × per-token rate), top flagged topics.

**E-FR-054** The AI Workspace shall display a thumbs-up / thumbs-down feedback control on each AI response. Feedback shall be persisted to `ai_chat_messages.user_feedback` (enum: POSITIVE, NEGATIVE, NULL).

---

## Non-Functional Requirements

**E-NFR-001** The backend API shall respond to 95% of non-AI requests within 500ms under a load of 50 concurrent users.

**E-NFR-002** AI streaming shall begin delivering the first token within 3 seconds of request submission under normal network conditions.

**E-NFR-003** The system shall support at least 5 concurrent institutions with 10 concurrent AI Workspace sessions each (50 total) without degradation.

**E-NFR-004** Database migrations shall be tested in a staging environment before applying to production.

**E-NFR-005** All background tasks shall complete or fail within 5 minutes; tasks exceeding this limit shall be automatically cancelled and logged.

**E-NFR-006** The system shall retain AI audit logs for a minimum of 5 years per POPIA data retention requirements.

**E-NFR-007** Audit reports generated in PDF or DOCX format shall be produced within 30 seconds for reports covering up to 200 findings.

**E-NFR-008** The frontend shall achieve a Lighthouse Performance score of ≥ 80 on desktop for the dashboard and AI Workspace pages.

**E-NFR-009** File uploads shall support files up to 50 MB. Files larger than 50 MB shall be rejected with a clear user-facing error message before upload begins.

**E-NFR-010** The system shall have ≥ 99.5% uptime during pilot operation (scheduled maintenance windows excluded).

---

## Security Requirements

**E-SEC-001** All production traffic shall be served over HTTPS (TLS 1.2 minimum, TLS 1.3 preferred). HTTP shall redirect to HTTPS.

**E-SEC-002** Application secrets shall never be committed to the git repository. A pre-commit hook or CI check shall block commits containing patterns matching secret formats.

**E-SEC-003** The system shall pass OWASP Top 10 assessment for: injection, broken authentication, sensitive data exposure, XML external entities, broken access control, security misconfiguration, XSS, insecure deserialisation, known vulnerable components, insufficient logging.

**E-SEC-004** All dependency vulnerabilities rated HIGH or CRITICAL shall be remediated before pilot deployment (`pip audit`, `npm audit`).

**E-SEC-005** Session cookies shall use `SameSite=Strict`, `Secure`, `HttpOnly` attributes.

**E-SEC-006** The system shall log all authentication events (login, logout, failed login, MFA failure) to the audit log with timestamp and IP address.

**E-SEC-007** Cross-tenant data access attempts shall be logged as security events and trigger an in-app alert to the System Administrator.

**E-SEC-008** AI provider API keys shall be rotated on a schedule defined in the secrets management policy (minimum quarterly).

---

## Governance Requirements

**E-GOV-001** A Data Protection Impact Assessment (DPIA) shall be completed and documented before any real personal data is processed in the pilot environment.

**E-GOV-002** A data retention schedule shall be implemented for: user records (duration of employment + 5 years), audit records (7 years), AI conversation records (5 years), uploaded evidence files (7 years or per institution policy).

**E-GOV-003** The system shall provide a data subject access request (DSAR) export: a single-click export of all personal data held for a named user, in JSON format, downloadable by the System Administrator.

**E-GOV-004** All AI-generated audit findings shall be clearly labelled `AI-assisted` in the UI and in exported documents, with a disclaimer that findings require human review before official action.

**E-GOV-005** The system shall maintain an AI governance policy document (human-readable) describing: model providers used, data sent to providers, retention policy for AI inputs/outputs, hallucination risk management, and human oversight requirements.

**E-GOV-006** No real student personal records shall appear in test data, seed data, or development environments. All test data shall use fictional identifiers.

---

## Data Requirements

**E-DATA-001** Regulatory documents indexed into Qdrant shall include metadata: `source_status`, `issuing_body`, `document_version`, `effective_date`, `institution_id` (null for national frameworks), `indexed_at`, `indexed_by`.

**E-DATA-002** The `CorrectiveAction` table shall be append-only for status history — no `UPDATE` on history records; new status changes create a `CorrectiveActionHistory` row.

**E-DATA-003** The `AiAuditLog` table shall be append-only. No UPDATE or DELETE operations shall be permitted on audit log rows via the application API.

**E-DATA-004** The pilot consent record (`PilotConsent`) shall capture: institution name, signatory name, signatory role, consent date, data processing scope, retention period agreed, POPIA acknowledgement flag.

**E-DATA-005** Analytics data shall be pre-aggregated in scheduled background jobs and cached in Redis for dashboard queries, with a staleness TTL of 1 hour.

---

## User Experience Requirements

**E-UX-001** The system shall restore `activeModuleId` from session history on page reload, if the session was last associated with a specific module.

**E-UX-002** First-time users (first login) shall see a guided onboarding tour (max 5 steps) tailored to their role, dismissable at any step.

**E-UX-003** The system shall achieve WCAG 2.1 AA compliance: 0 Level A failures, ≤ 5 Level AA failures, in an internal audit conducted before pilot launch.

**E-UX-004** The HOD home page shall display a department compliance score, recent unresolved findings count, and an audit activity feed for the current academic period.

**E-UX-005** The Faculty Dean home page shall display a faculty-level compliance heat map by department, with drill-down to department level.

**E-UX-006** All AI response cards in the workspace shall include a user feedback control (POSITIVE / NEGATIVE) accessible via keyboard.

**E-UX-007** The compliance heat map shall render correctly on viewport widths ≥ 768px (tablet minimum).

---

## Operational Requirements

**E-OPS-001** The system shall produce structured JSON log output with fields: `timestamp`, `level`, `correlation_id`, `institution_id` (where applicable), `user_id` (where applicable), `event`, `detail`, `duration_ms`.

**E-OPS-002** The backend shall expose a Prometheus-compatible metrics endpoint at `GET /metrics` (protected by a metrics API key, not user auth).

**E-OPS-003** A daily automated database backup shall dump the PostgreSQL database to a configurable backup destination and verify the dump is non-empty.

**E-OPS-004** An automated Qdrant snapshot shall be triggered nightly via the background scheduler.

**E-OPS-005** A production Docker Compose file (`docker-compose.prod.yml`) shall define resource limits: backend CPU ≤ 2 cores, memory ≤ 2 GB; PostgreSQL CPU ≤ 2 cores, memory ≤ 4 GB; Redis memory ≤ 512 MB; Qdrant memory ≤ 2 GB.

**E-OPS-006** A CI/CD pipeline (GitHub Actions) shall run on every push to `main` and `feature/*` branches: install dependencies, run full backend test suite, run `tsc --noEmit`, run `npm run build`. Failures shall block merge.

**E-OPS-007** A staging environment configuration shall be maintained, separate from production, using distinct secrets and database instances.

**E-OPS-008** A runbook shall document: how to roll back a failed migration, how to restore from a database backup, how to restart the Qdrant collection from source documents, how to rotate secrets, how to respond to a security incident.

---

## Evaluation and Pilot Requirements

**E-EVAL-001** The pilot shall target at least 1 institution with at least 5 active users spanning at least 3 roles (QA Officer, Programme Coordinator, Lecturer).

**E-EVAL-002** The pilot shall run for a minimum of 30 days of active use before the exit survey is administered.

**E-EVAL-003** Pilot success shall be measured against the 25+ metrics defined in [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md).

**E-EVAL-004** The pilot shall produce a lessons-learned document capturing: what worked, what failed, what must be fixed before commercial launch, and what should be deferred.

**E-EVAL-005** All pilot participants shall sign a consent and NDA document before accessing the system. Consent shall be recorded in the `PilotConsent` table.

**E-EVAL-006** The AQAA Engineering team shall conduct a weekly sync with at least one pilot institution contact throughout the pilot period.

**E-EVAL-007** The pilot shall have a documented rollback procedure that can restore the institution to pre-pilot state within 4 hours if required.
