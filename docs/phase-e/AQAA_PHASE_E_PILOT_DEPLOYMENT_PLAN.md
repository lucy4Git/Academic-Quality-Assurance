# AQAA Phase E — Pilot Deployment Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Pilot Objectives

1. Deploy AQAA in a controlled real-world environment with at least one South African HEI
2. Validate that the platform functions correctly for real QA workflows, not only test scenarios
3. Collect baseline metrics against the evaluation plan
4. Identify defects and gaps that did not surface in development testing
5. Produce the evidence base required for commercial launch decision

---

## 2. Pilot Eligibility Criteria

An institution qualifies as a pilot institution if it meets all of the following:

| Criterion | Minimum |
|-----------|---------|
| Institution type | Registered South African HEI (public or private) |
| QA function | Active Quality Assurance Officer or equivalent |
| Technical capability | Internet-connected devices for all pilot users; dedicated technical contact |
| Engagement commitment | 30+ days active use; participation in exit survey and interview |
| Data governance | Institution signs Data Processing Agreement and Pilot Consent record |
| Risk acceptance | Institution understands AQAA is a pilot system; findings are advisory only |

---

## 3. Pilot Cohort Design

### Minimum cohort (Sprint E7)

| Role | Count | Selection Criteria |
|------|-------|-------------------|
| Quality Assurance Officer | 1–2 | Primary pilot users; must cover the finding lifecycle |
| Programme Coordinator | 2–3 | Must cover at least 2 active programmes |
| Lecturer | 3–5 | Must have active module folders with real evidence |
| Head of Department | 1 | Optional but recommended |
| Faculty Dean | 1 | Optional but recommended |
| System Admin | 1 | Institution technical contact |

**Total minimum:** 8 active pilot users.

### Modules and programmes to include
- Minimum: 6 modules across 2 programmes
- At least one programme that is approaching an accreditation review cycle (to validate accreditation readiness agent)

---

## 4. Pre-Pilot Checklist

### Technical Readiness (AQAA Engineering)

- [ ] All 18 P0 pilot-blocking gaps closed (see commercial gap analysis)
- [ ] Production Docker Compose deployed on pilot server
- [ ] TLS certificate active (Caddy automatic HTTPS)
- [ ] Backend test suite passes: `python -m pytest -q` (0 failures)
- [ ] TypeScript: `tsc --noEmit` (0 errors)
- [ ] Production build: `npm run build` (clean)
- [ ] Database backup automated and verified for at least 3 consecutive days
- [ ] Qdrant snapshot schedule operational
- [ ] Structured logging operational (JSON output to log file)
- [ ] Sentry integration active (test error captured and visible in Sentry dashboard)
- [ ] Rate limiting verified (`locust` or equivalent load test)
- [ ] Virus scanning enabled and tested
- [ ] OFFICIAL_VERIFIED regulatory documents indexed: CHE, DHET, SAQA
- [ ] Pilot institution provisioned via tenant provisioning API
- [ ] Pilot users created and roles assigned
- [ ] Pilot consent record created in database
- [ ] Staging environment available for AQAA Engineering testing separate from pilot

### Institutional Readiness (Pilot Institution)

- [ ] Data Processing Agreement signed by authorised signatory
- [ ] Pilot Consent record signed (`PilotConsent` database entry created)
- [ ] IT contact briefed on server access and escalation path
- [ ] All pilot users have received onboarding credentials
- [ ] Institutional policy documents uploaded (if available)
- [ ] Module records and evidence files uploaded for pilot modules
- [ ] Pilot institution IKP setup completed (Qdrant collection for institution-specific docs)

---

## 5. Onboarding Protocol

### Day 0 — Institution Setup (AQAA Engineering)
1. Provision institution via `/api/v1/institutions/` (POST)
2. Create pilot user accounts via admin panel
3. Assign roles to pilot users
4. Index institution-specific policy documents (if provided)
5. Verify QA Officer login → AI Workspace context loads correctly for their institution
6. Confirm module records exist and are associated with the institution

### Day 1 — Guided Onboarding Session (60 min, all pilot users)
- Live walkthrough of role-specific home page
- QA Officer: demonstrate compliance dashboard → AI Workspace → finding lifecycle
- Lecturer: demonstrate module dashboard → evidence upload → AI compliance query
- Explain onboarding tour (5-step overlay on next login)
- Explain how to flag an AI hallucination (thumbs-down + "Report inaccuracy")
- Share support contact details (email/WhatsApp for pilot period)
- Confirm all users can log in and access their expected views

### Day 2–30 — Active Pilot Period
- No AQAA Engineering involvement unless escalated
- Automated: daily database backup, Qdrant snapshot, scheduled audit triggers if configured
- Weekly: AQAA Engineering reviews metrics dashboard (M-01 through M-25); notes anomalies
- Weekly: AI output sample review (20 responses)
- Week 3: Mid-pilot check-in call with institution contact (30 min)

---

## 6. Support Protocol During Pilot

| Support Type | Channel | Response Time |
|-------------|---------|--------------|
| Login/access issue | Email + WhatsApp | 2 hours |
| Platform error (5xx) | Email + WhatsApp | 4 hours |
| Data concern | Email | 24 hours |
| Feature question | Email | Next business day |
| Security incident | Direct call | 1 hour |

**Escalation path:**
1. Pilot user → Institution Technical Contact
2. Institution Technical Contact → AQAA Engineering (email/WhatsApp)
3. Critical security incident → AQAA Engineering direct call

---

## 7. Rollback Procedure

If a critical defect is discovered during the pilot, the following procedure is used:

### Rollback Decision Authority
- AQAA Engineering can initiate rollback without institution approval for: P0 security incidents, data corruption, service outage > 4 hours
- Institution may request rollback at any time

### Rollback Steps
1. Notify institution contact by phone
2. Stop backend: `docker compose stop backend`
3. Backup current database state: `docker exec aqaa-postgres pg_dump -U aqaa aqaa > backup_pre_rollback.sql`
4. Roll back migrations if required: `python -m alembic downgrade -1`
5. Restore previous code version from git tag
6. Restart: `docker compose up -d`
7. Verify health: `GET /health`
8. Notify institution contact of restoration and estimated timeline for fix

**Maximum rollback time target:** 4 hours from decision to service restoration.

---

## 8. Data Handling During Pilot

### What AQAA Engineering may access
- Log files (structured JSON — no user content, only metadata)
- Prometheus metrics (aggregate only)
- Sentry error traces (stack traces only — no user data)
- Database records with prior written institution approval for debugging specific issues

### What AQAA Engineering may NOT access without explicit institution consent
- AI conversation content
- Uploaded evidence files
- Finding details
- User personal information beyond what was agreed in the DPA

### Data at end of pilot
- All institution data retained for 30 days post-pilot
- Institution may request export of all their data (JSON) at any point
- After 30 days post-pilot, institution data is deleted unless continued use is agreed

---

## 9. Lessons-Learned Protocol

Conducted in Week 5 (7 days after pilot end). Attendees: AQAA Engineering + Institution Technical Contact + at least 1 QA Officer.

**Agenda (90 min):**
1. Metrics review (30 min): walk through M-01 to M-25 with actuals vs benchmarks
2. Exit survey results summary (20 min)
3. Incident review (10 min): any incidents that occurred and how they were handled
4. Open discussion — what worked (10 min)
5. Open discussion — what didn't work (15 min)
6. Commercial launch recommendations (5 min)

**Output document:** `docs/phase-e/pilot/AQAA_PILOT_{INSTITUTION_CODE}_LESSONS_LEARNED.md`

---

## 10. Go/No-Go for Commercial Launch

After pilot evaluation summary is complete:

| Outcome | Decision |
|---------|---------|
| Pilot Pass | Proceed to Phase F commercial launch planning |
| Pilot Conditional Pass | Remediate mandatory items; no re-pilot required if all P0 gaps closed |
| Pilot Fail | Halt; root cause analysis; second pilot after minimum 4-week remediation |

---

## Referenced Documents

- [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md) — Success metrics
- [AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md](AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md) — Incident response
- [AQAA_PHASE_E_DATA_REQUIREMENTS.md](AQAA_PHASE_E_DATA_REQUIREMENTS.md) — PilotConsent schema
