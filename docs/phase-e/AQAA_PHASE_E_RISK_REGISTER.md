# AQAA Phase E — Risk Register

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## Legend

**Probability:** 1 (rare) → 5 (almost certain)
**Impact:** 1 (negligible) → 5 (critical/project-ending)
**Risk Score:** Probability × Impact
**Priority:** P0 (score ≥ 16), P1 (score 9–15), P2 (score 4–8), P3 (score < 4)

---

## Risk Register

### R-01 — AI Hallucination in Regulatory Guidance
**Category:** AI Quality
**Probability:** 3 | **Impact:** 5 | **Score:** 15 | **Priority:** P1

**Description:** The AI Workspace generates incorrect regulatory claims (e.g., misquotes a CHE criterion or cites a superseded policy), and a pilot user acts on this information without further verification.

**Mitigation:**
- Grounding coverage target: ≥ 85% OFFICIAL_VERIFIED citations
- All AI responses labelled "AI-assisted — requires human review before official action"
- Hallucination flagging mechanism for all users
- Weekly AI output sample review by AQAA Engineering
- Source status badges on all citations

**Contingency:** If confirmed hallucination rate exceeds 3 per 1,000, suspend AI Workspace for affected regulatory domain; notify pilot institution; update prompt templates; re-verify before resuming.

---

### R-02 — Security Breach or Cross-Tenant Data Access
**Category:** Security
**Probability:** 2 | **Impact:** 5 | **Score:** 10 | **Priority:** P1

**Description:** An attacker or misconfigured tenant user accesses data belonging to another institution.

**Mitigation:**
- Existing `institution_id` row-level filtering in all queries
- Cross-tenant requests return 404 (no existence leaking)
- Rate limiting prevents brute-force session probing
- MFA for elevated roles
- Pre-pilot penetration test (internal, per security plan)
- Security event logging and real-time alert to System Admin

**Contingency:** Immediate service suspension; incident response procedure activated; POPIA Information Regulator notification within 72 hours if personal data exposed; affected institution notified.

---

### R-03 — Pilot Institution Disengagement
**Category:** Pilot
**Probability:** 3 | **Impact:** 4 | **Score:** 12 | **Priority:** P1

**Description:** The pilot institution's QA Officer or key users disengage during the pilot (role change, workload, system frustration), leaving insufficient usage data for meaningful evaluation.

**Mitigation:**
- Select pilot institution with demonstrated QA function and engaged contact
- AQAA Engineering maintains weekly contact throughout pilot
- Mid-pilot check-in at week 3 to identify issues early
- Onboarding support for first 2 weeks

**Contingency:** If primary QA Officer disengages, substitute with Head of Department or Programme Coordinator as primary user. If engagement drops below 3 sessions/user/week by week 2, schedule 1-hour problem-solving session with institution contact.

---

### R-04 — Regulatory Document Unavailability
**Category:** Regulatory Knowledge
**Probability:** 2 | **Impact:** 4 | **Score:** 8 | **Priority:** P2

**Description:** Key CHE/DHET/SAQA documents are not freely available for indexing (gated, restricted, or unclear copyright), preventing OFFICIAL_VERIFIED grounding before pilot.

**Mitigation:**
- Early download of all target documents (Sprint E1)
- Check each document's copyright notice before indexing
- Fallback: use OFFICIAL_UNVERIFIED status and indicate status clearly in UI

**Contingency:** If a key document cannot be indexed as OFFICIAL_VERIFIED, use OFFICIAL_UNVERIFIED and increase the prominence of the "verify independently" UI warning. Seek written permission from issuing body for indexing.

---

### R-05 — Background Scheduler Failure Causes Missed Audits
**Category:** Platform
**Probability:** 3 | **Impact:** 3 | **Score:** 9 | **Priority:** P1

**Description:** The ARQ background scheduler fails silently, causing scheduled audit triggers to not fire and pilot users to not receive automated audit notifications.

**Mitigation:**
- Background job log with status tracking
- Prometheus alert if no jobs complete within a configured threshold
- Sentry captures ARQ task exceptions
- Daily job health check included in operational runbook

**Contingency:** Fallback to manual audit triggers; notify pilot users; investigate job log and Sentry for root cause.

---

### R-06 — Database Migration Failure on Pilot Server
**Category:** Operations
**Probability:** 2 | **Impact:** 4 | **Score:** 8 | **Priority:** P2

**Description:** A Phase E migration fails on the pilot server due to schema state mismatch or Postgres version difference.

**Mitigation:**
- All migrations tested in staging environment first
- Migration validation: `alembic current` verified before going live
- Database backup taken immediately before each migration run
- Rollback procedure documented in runbook

**Contingency:** Restore from pre-migration backup; apply migration fix; re-migrate.

---

### R-07 — AI Provider Outage
**Category:** AI / External Dependency
**Probability:** 2 | **Impact:** 3 | **Score:** 6 | **Priority:** P2

**Description:** Primary AI provider (Anthropic/OpenAI) experiences an outage, making the AI Workspace unavailable during the pilot.

**Mitigation:**
- Primary + secondary provider configured in `llm_router_service.py`
- Automatic failover on HTTP 5xx or timeout

**Contingency:** If both providers down, AI Workspace shows "AI unavailable — try again shortly" message. All other QA functions (audit reports, finding management, evidence upload) remain operational.

---

### R-08 — POPIA Non-Compliance Discovery During Pilot
**Category:** Governance / Legal
**Probability:** 2 | **Impact:** 5 | **Score:** 10 | **Priority:** P1

**Description:** After pilot begins, a POPIA compliance gap is discovered (e.g., personal data sent to AI provider without adequate DPA, or insufficient consent for processing).

**Mitigation:**
- DPIA completed before pilot go-live
- Data Processing Agreement signed with pilot institution before any personal data processed
- No student personal identifiers included in AI prompts (prompt sanitisation)
- AI provider DPA in place before pilot

**Contingency:** Suspend processing of affected personal data category; consult POPIA legal advice; notify institution; notify Information Regulator if required.

---

### R-09 — Pilot User Data Entry Errors Corrupt Evaluation Data
**Category:** Data Quality
**Probability:** 3 | **Impact:** 2 | **Score:** 6 | **Priority:** P2

**Description:** Pilot users enter test or incorrect data, making evaluation metrics unreliable (e.g., closing all findings as resolved on day 1 to explore the workflow).

**Mitigation:**
- Clear onboarding guidance: "Use real or realistic module scenarios where possible"
- AQAA Engineering reviews engagement metrics weekly; flags anomalies
- Evaluation plan separates behavioural metrics (hard to fake) from outcome metrics (easier to game)

**Contingency:** Exclude outlier sessions from quantitative analysis; weight qualitative evidence more heavily.

---

### R-10 — Performance Degradation Under Pilot Load
**Category:** Platform
**Probability:** 2 | **Impact:** 3 | **Score:** 6 | **Priority:** P2

**Description:** The pilot server cannot handle 50 concurrent sessions, causing slow responses or timeouts that impair pilot users' experience.

**Mitigation:**
- Load test with Locust before pilot go-live (E-OPS requirement)
- Docker resource limits configured (CPU and memory per service)
- Redis caching for analytics queries
- Background tasks run in worker process (not in API process)

**Contingency:** Identify bottleneck via Prometheus metrics; scale vertical (larger server) for pilot duration; note horizontal scaling requirements for Phase F.

---

### R-11 — IKP Processing Errors for Institutional Documents
**Category:** Regulatory Knowledge
**Probability:** 2 | **Impact:** 3 | **Score:** 6 | **Priority:** P2

**Description:** Institutional policy documents uploaded during the pilot fail to index correctly (corrupted PDF, incorrect chunk extraction, wrong institution_id) causing citation failures.

**Mitigation:**
- Document processing pipeline tested with TUT/UP IKPs in Phase D
- Error status visible in RegulatoryDocumentRegistry (`ingestion_failed`)
- Operator can re-trigger ingestion after fixing the document

**Contingency:** Manual re-upload and re-index; if repeated failure, exclude document from Qdrant for pilot duration.

---

### R-12 — Pilot Server Disk Space Exhaustion
**Category:** Operations
**Probability:** 2 | **Impact:** 3 | **Score:** 6 | **Priority:** P2

**Description:** Uploaded evidence files, database backups, and Qdrant data fill the pilot server's storage, causing the system to fail.

**Mitigation:**
- Storage monitoring via Prometheus (disk usage alert at 80%)
- Upload size limit: 50 MB per file
- Daily backups stored to external destination (not same disk)
- Qdrant snapshots stored to separate volume

**Contingency:** Free disk space by removing old backup files (retain latest 7); increase server storage if needed.

---

### R-13 — Scope Creep from Pilot Feedback
**Category:** Project Management
**Probability:** 4 | **Impact:** 2 | **Score:** 8 | **Priority:** P2

**Description:** Pilot users request features outside Phase E scope (e.g., SSO, multi-institution dashboards, mobile app), diverting engineering time during the pilot period.

**Mitigation:**
- Scope document shared with pilot institution before onboarding
- All feedback captured in lessons-learned; explicitly noted as "in scope for Phase F" or "deferred"
- No feature development during active pilot period

**Contingency:** Politely defer all feature requests to Phase F backlog; document in lessons-learned.

---

### R-14 — Qdrant Vector Search Quality Degrades
**Category:** AI Quality
**Probability:** 2 | **Impact:** 3 | **Score:** 6 | **Priority:** P2

**Description:** As more documents are indexed, Qdrant HNSW index quality degrades (false negatives in search), causing relevant regulatory clauses to not appear in AI citations.

**Mitigation:**
- HNSW parameters reviewed before pilot (ef_construction, m values)
- Grounding coverage metric (M-16) monitored weekly; alerts if drops below 80%
- Collection-level search quality tested with standard query set before pilot go-live

**Contingency:** Re-optimise HNSW parameters; rebuild collection index if severe degradation detected.

---

### R-15 — PDF Export Library Incompatibility
**Category:** Technical
**Probability:** 2 | **Impact:** 2 | **Score:** 4 | **Priority:** P3

**Description:** Chosen PDF library (WeasyPrint or ReportLab) has rendering issues with complex tables or Arabic/Afrikaans characters in institutional content.

**Mitigation:**
- Test PDF export with sample report containing full character set before pilot
- Alternative: fall back to ReportLab if WeasyPrint renders incorrectly

**Contingency:** Defer PDF export for pilot (use DOCX and CSV); fix rendering in sprint after pilot.

---

### R-16 — Single Institution Pilot Is Insufficient for Generalisation
**Category:** Evaluation
**Probability:** 3 | **Impact:** 2 | **Score:** 6 | **Priority:** P2

**Description:** Evaluation metrics from a single institution may not reflect the diversity of South African HEIs, leading to commercial launch decisions based on an unrepresentative sample.

**Mitigation:**
- Select pilot institution that represents the broadest reasonable case (medium-sized, multi-faculty, mixed programme types)
- Note in evaluation plan that findings apply to the specific pilot context
- Plan for second pilot institution in Phase F if budget and timeline allow

**Contingency:** Explicitly scope commercial launch claims to institutions similar to the pilot institution; second pilot before broader rollout.

---

## Risk Summary Matrix

| ID | Risk | Score | Priority |
|----|------|-------|---------|
| R-01 | AI Hallucination in Regulatory Guidance | 15 | P1 |
| R-02 | Security Breach / Cross-Tenant Access | 10 | P1 |
| R-03 | Pilot Institution Disengagement | 12 | P1 |
| R-04 | Regulatory Document Unavailability | 8 | P2 |
| R-05 | Background Scheduler Failure | 9 | P1 |
| R-06 | Database Migration Failure | 8 | P2 |
| R-07 | AI Provider Outage | 6 | P2 |
| R-08 | POPIA Non-Compliance Discovery | 10 | P1 |
| R-09 | Pilot Data Entry Errors | 6 | P2 |
| R-10 | Performance Degradation | 6 | P2 |
| R-11 | IKP Processing Errors | 6 | P2 |
| R-12 | Disk Space Exhaustion | 6 | P2 |
| R-13 | Scope Creep from Pilot Feedback | 8 | P2 |
| R-14 | Qdrant Search Quality Degradation | 6 | P2 |
| R-15 | PDF Export Library Issues | 4 | P3 |
| R-16 | Single-Institution Generalisation | 6 | P2 |

**P1 risks (top priority):** R-01, R-02, R-03, R-05, R-08

---

## Referenced Documents

- [AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md](AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md) — Incident response
- [AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md](AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md) — Rollback procedure
- [AQAA_PHASE_E_EVALUATION_PLAN.md](AQAA_PHASE_E_EVALUATION_PLAN.md) — AI quality metrics
