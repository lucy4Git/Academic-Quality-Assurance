# AQAA Phase E — Acceptance Criteria

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

> Phase E is not complete until every criterion in this document passes. All must be verified by AQAA Engineering before the Phase E git tag is created.

---

## 1. Feature Acceptance Criteria

### 1.1 Security and Infrastructure

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-SEC-01 | All API endpoints rate-limited (200/min auth, 30/min unauth) | `curl` rate limit test: 201st request returns HTTP 429 | ☐ |
| AC-SEC-02 | HTTPS enforced; HTTP redirects to HTTPS | `curl http://` → HTTP 301 or 308 to HTTPS | ☐ |
| AC-SEC-03 | Secrets not in docker-compose.prod.yml or any committed file | `git log --all --diff-filter=A -- '*.env*'` + grep scan | ☐ |
| AC-SEC-04 | Virus scanning enabled in production config | Upload EICAR test file; confirm file transitions to `quarantined` | ☐ |
| AC-SEC-05 | Logout invalidates token immediately | Login → logout → use access_token → HTTP 401 | ☐ |
| AC-SEC-06 | MFA enforced for QA_OFFICER and above | Login as QA_OFFICER without MFA → prompted to enroll | ☐ |
| AC-SEC-07 | Storage paths include institution_id | Upload file; verify path contains institution UUID | ☐ |
| AC-SEC-08 | CI pipeline runs on every push; failures block merge | Push failing test to feature branch; PR blocked | ☐ |
| AC-SEC-09 | No HIGH or CRITICAL dependency vulnerabilities | `pip audit` and `npm audit` both exit 0 in CI | ☐ |
| AC-SEC-10 | Production Docker Compose runs with TLS | `docker compose -f docker-compose.prod.yml up -d`; HTTPS accessible | ☐ |

### 1.2 Background Processing

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-BG-01 | ARQ worker starts with backend and persists across restart | Stop and start worker; verify queued job executes | ☐ |
| AC-BG-02 | Scheduled audit trigger fires at configured time | Set next_run_at to 2 minutes from now; verify audit_runs record created | ☐ |
| AC-BG-03 | Failed task retried 3 times with increasing delays | Inject task failure; verify 3 retry attempts in background_job_logs | ☐ |
| AC-BG-04 | Daily database backup produces valid SQL file | Trigger backup job; verify SQL file is non-empty and can be restored | ☐ |
| AC-BG-05 | Nightly Qdrant snapshot completes without error | Trigger snapshot job; verify no error in background_job_logs | ☐ |

### 1.3 Regulatory Knowledge

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-REG-01 | CHE HEQSF indexed as OFFICIAL_VERIFIED | Query: "What are the CHE criteria for NQF Level 7?"; verify citation with source_status=OFFICIAL_VERIFIED | ☐ |
| AC-REG-02 | DHET Teacher Education Policy indexed as OFFICIAL_VERIFIED | Query: "minimum qualification for a teacher educator"; verify OFFICIAL_VERIFIED citation | ☐ |
| AC-REG-03 | SAQA NQF Descriptors indexed as OFFICIAL_VERIFIED | Query: "NQF Level 8 descriptor"; verify OFFICIAL_VERIFIED citation | ☐ |
| AC-REG-04 | Institutional policy can be uploaded and queried | Upload a test policy PDF as SYSTEM_ADMIN; query related topic; verify INSTITUTIONAL_APPROVED citation | ☐ |
| AC-REG-05 | Superseded document excluded from new queries | Mark a document SUPERSEDED; query topic; verify it does not appear in citations | ☐ |

### 1.4 Analytics and Reporting

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-ANA-01 | Compliance trend chart renders 12 data points | Navigate to `/analytics`; chart shows 12 weeks of data | ☐ |
| AC-ANA-02 | Faculty heat map renders correct colour scale | Navigate to `/analytics/heat-map`; critical faculty shows red, compliant shows green | ☐ |
| AC-ANA-03 | PDF report generates and is a valid PDF file | `GET /api/v1/reports/{id}?format=pdf`; response Content-Type: application/pdf; file opens in PDF viewer | ☐ |
| AC-ANA-04 | DOCX report generates and is a valid Word document | `GET /api/v1/reports/{id}?format=docx`; file opens in Microsoft Word without corruption | ☐ |
| AC-ANA-05 | XLSX export includes correct columns | `GET /api/v1/reports/{id}/findings?format=xlsx`; file has columns: finding_id, title, severity, status, etc. | ☐ |
| AC-ANA-06 | Audit cycle comparison renders side-by-side scores | Select two 30-day periods in comparison view; both periods shown | ☐ |

### 1.5 AI Governance

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-GOV-01 | Every ask-stream call creates an ai_audit_logs record | Make AI query; check database: `SELECT COUNT(*) FROM ai_audit_logs` increases by 1 | ☐ |
| AC-GOV-02 | Hallucination can be flagged and triaged | Flag response as hallucination; System Admin sees it in governance dashboard; can mark REVIEWED | ☐ |
| AC-GOV-03 | AI responses labelled with grounding classification | OFFICIAL_VERIFIED citation → "Grounded" badge; no sources → "Ungrounded" badge | ☐ |
| AC-GOV-04 | User feedback (thumbs up/down) persists | Click thumbs down; refresh page; `user_feedback = NEGATIVE` in database | ☐ |
| AC-GOV-05 | DSAR export produces valid JSON | `GET /admin/users/{id}/export`; JSON contains all personal data fields for that user | ☐ |

### 1.6 Corrective Actions

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-CA-01 | Corrective action can be created linked to a finding | `POST /api/v1/corrective-actions/` with valid finding_id; 201 Created | ☐ |
| AC-CA-02 | Corrective action status lifecycle enforces transitions | Attempt OPEN → CLOSED without going through IN_PROGRESS; verify rejection | ☐ |
| AC-CA-03 | Overdue job marks past-due actions correctly | Create action with due_date = yesterday; run overdue job; status = OVERDUE | ☐ |
| AC-CA-04 | In-app notification sent at 3-day warning | Create action with due_date = 3 days from now; run notification job; notification created | ☐ |
| AC-CA-05 | History records are immutable (no delete) | `DELETE /api/v1/corrective-actions/{id}/history/{history_id}` → HTTP 405 | ☐ |

### 1.7 User Experience

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-UX-01 | Module context restored on page reload | Set activeModuleId in workspace; reload page; context panel shows same module | ☐ |
| AC-UX-02 | Onboarding tour displays on first login | Create new user; log in; overlay tour appears at step 1 | ☐ |
| AC-UX-03 | Onboarding tour is role-specific | QA Officer tour step 2 differs from Lecturer tour step 2 | ☐ |
| AC-UX-04 | Dean home page shows faculty heat map | Log in as FACULTY_DEAN; home page includes heat map component | ☐ |
| AC-UX-05 | HOD home page shows department compliance trend | Log in as HEAD_OF_DEPARTMENT; home page shows trend data | ☐ |

### 1.8 Pilot

| ID | Criterion | Verification Method | Pass |
|----|-----------|-------------------|------|
| AC-PILOT-01 | Pilot institution provisionable via admin wizard | Create a new institution end-to-end via `/admin/institutions/new` | ☐ |
| AC-PILOT-02 | IKP auto-setup runs as part of provisioning | After provisioning, Qdrant collection exists for new institution | ☐ |
| AC-PILOT-03 | Pilot consent record saved | `POST /api/v1/consent/pilot`; record in `pilot_consent` table | ☐ |
| AC-PILOT-04 | Pilot completed with minimum cohort | At least 8 users across 3+ roles active for 30+ days | ☐ |

---

## 2. Non-Functional Acceptance Criteria

| ID | Criterion | Target | Verification |
|----|-----------|--------|-------------|
| AC-NFR-01 | Backend test suite passes | 0 failures | `python -m pytest -q` |
| AC-NFR-02 | TypeScript 0 errors | 0 errors | `tsc --noEmit` |
| AC-NFR-03 | Production build clean | No build errors | `npm run build` |
| AC-NFR-04 | API P95 response time under load | ≤ 500ms at 50 concurrent users | `locust` load test |
| AC-NFR-05 | AI time-to-first-token | ≤ 3s median | Prometheus metric |
| AC-NFR-06 | System uptime during pilot | ≥ 99.5% | Prometheus uptime |
| AC-NFR-07 | PDF report generation time | ≤ 30s for 200-finding report | Timed API call |
| AC-NFR-08 | WCAG 2.1 AA | 0 Level A failures | Internal audit |

---

## 3. Tenant Isolation Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|-------------|
| AC-TEN-01 | Session owned by Institution A is 403 for Institution B user | Create sessions for each; verify cross-access returns 403 |
| AC-TEN-02 | Module owned by Institution A is 404 for Institution B user | Verify module ID from A returns 404 when queried by B's JWT |
| AC-TEN-03 | Qdrant query does not return results from another institution | Run AI query from Institution B; verify no sources from Institution A's collection appear |
| AC-TEN-04 | Uploaded file from Institution A is not accessible to Institution B | Get presigned URL for Institution A file using Institution B JWT → 403 |

---

## 4. AI Governance Acceptance Criteria

| ID | Criterion | Target |
|----|-----------|--------|
| AC-AIGG-01 | Grounding coverage during pilot | ≥ 85% of responses cite ≥1 OFFICIAL_VERIFIED source |
| AC-AIGG-02 | Confirmed hallucination rate during pilot | ≤ 1 per 1,000 responses |
| AC-AIGG-03 | AI output labelling | 100% of AI responses show grounding classification badge |
| AC-AIGG-04 | AI audit log completeness | 100% of ask-stream calls produce an ai_audit_logs record |
| AC-AIGG-05 | AI governance policy document exists | `docs/governance/AI_GOVERNANCE_POLICY.md` present and reviewed |

---

## 5. Pilot Evaluation Acceptance Criteria

| ID | Criterion | Target |
|----|-----------|--------|
| AC-EVAL-01 | Exit survey Q6 (would recommend) | Average ≥ 4.0/5.0 |
| AC-EVAL-02 | Exit survey Q3 (trust in citations) | Average ≥ 3.8/5.0 |
| AC-EVAL-03 | AI positive feedback rate | ≥ 80% |
| AC-EVAL-04 | Compliance score trend | Score at day 30 ≥ score at day 1 for pilot institution |
| AC-EVAL-05 | Lessons-learned document complete | Document exists with all required sections |
| AC-EVAL-06 | No unresolved P0 issues at pilot end | P0 column in gap analysis: all CLOSED |

---

## 6. Phase E Completion Gate

Phase E is declared **COMPLETE** when:

1. All AC-SEC-*, AC-BG-*, AC-REG-*, AC-ANA-*, AC-GOV-*, AC-CA-*, AC-UX-*, AC-PILOT-*, AC-NFR-*, AC-TEN-*, AC-AIGG-* criteria are ☑ (checked)
2. Pilot evaluation outcome is **PASS** or **CONDITIONAL PASS** (with remediations applied)
3. Exit survey administered and results documented
4. Lessons-learned document complete
5. Phase E release documentation complete (release notes, as-built, environment variables, migration validation, owner acceptance)
6. Phase E git tag `v1.0.0-phase-e` created pointing to the final Phase E commit

---

## Referenced Documents

- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md)
- [AQAA_PHASE_E_SPRINT_ROADMAP.md](AQAA_PHASE_E_SPRINT_ROADMAP.md)
- [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md)
- [AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md](AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md)
