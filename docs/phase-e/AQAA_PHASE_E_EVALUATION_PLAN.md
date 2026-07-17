# AQAA Phase E — Evaluation Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Evaluation Objectives

1. Determine whether AQAA reduces the time and effort required to conduct a quality assurance audit cycle
2. Measure the accuracy and reliability of AI-generated findings and regulatory citations
3. Assess whether pilot users can achieve their QA goals without external training or assistance
4. Identify defects, gaps, and usability failures before commercial launch
5. Establish a baseline for continuous improvement metrics in Phase F

---

## 2. Evaluation Framework

The evaluation combines:
- **Quantitative metrics** — automated, logged in the database and Prometheus
- **Qualitative measures** — exit survey, user interviews, session observation
- **AI-specific measures** — grounding coverage, hallucination rate, citation accuracy

Evaluation period: 30 days of active use per pilot institution.

---

## 3. Quantitative Metrics

### 3.1 Platform Health

| Metric | ID | Formula | Benchmark | Source |
|--------|-----|---------|-----------|--------|
| System uptime | M-01 | (minutes available / total minutes) × 100 | ≥ 99.5% | Prometheus |
| API P95 response time | M-02 | 95th percentile of response_duration_ms | ≤ 500ms | Prometheus |
| AI stream time-to-first-token | M-03 | Median time from request to first SSE token | ≤ 3s | Prometheus |
| Background task success rate | M-04 | completed / (completed + failed) × 100 | ≥ 98% | background_job_logs |
| Error rate | M-05 | 5xx responses / total responses × 100 | ≤ 0.5% | Prometheus |

### 3.2 Engagement

| Metric | ID | Formula | Benchmark | Source |
|--------|-----|---------|-----------|--------|
| Daily active users (DAU) | M-06 | Unique users with ≥1 AI session or API request per day | Baseline: all pilot users active within 7 days of onboarding | ai_chat_sessions |
| Weekly session count per user | M-07 | Total sessions / active users / weeks | ≥ 3 sessions/user/week for QA Officers | ai_chat_sessions |
| Average session length | M-08 | Median message count per session | ≥ 5 messages per session | ai_chat_messages |
| Audit trigger frequency | M-09 | Total audit triggers / days | At least 1 audit per module per 30-day period | audit_runs |
| Automated vs manual audit ratio | M-10 | background-triggered audits / total audits | ≥ 20% automated after scheduler enabled | audit_runs + background_job_logs |

### 3.3 Quality Assurance Outcomes

| Metric | ID | Formula | Benchmark | Source |
|--------|-----|---------|-----------|--------|
| Finding detection rate | M-11 | CRITICAL + HIGH findings per 10 modules audited | ≥ 2 findings per 10 modules (QA is not trivial) | findings |
| Finding resolution time (mean) | M-12 | AVG(closed_at - created_at) for CLOSED findings | ≤ 14 days for CRITICAL, ≤ 30 days for HIGH | findings |
| Corrective action completion rate | M-13 | CLOSED corrective_actions / total corrective_actions × 100 | ≥ 70% within pilot period | corrective_actions |
| Overdue corrective action rate | M-14 | OVERDUE corrective_actions / total open × 100 | ≤ 20% | corrective_actions |
| Compliance score trend | M-15 | Average compliance score at start vs end of pilot | Positive trend (score at day 30 ≥ score at day 1) | compliance_trend_snapshots |

### 3.4 AI Quality

| Metric | ID | Formula | Benchmark | Source |
|--------|-----|---------|-----------|--------|
| Grounding coverage | M-16 | % responses citing ≥1 OFFICIAL_VERIFIED source | ≥ 85% | ai_audit_logs |
| Zero-source rate | M-17 | % responses with no sources cited | ≤ 5% | ai_audit_logs |
| Hallucination incident rate | M-18 | Flagged incidents / 1,000 responses | ≤ 5 per 1,000 | hallucination_incidents |
| Confirmed hallucination rate | M-19 | Confirmed incidents / 1,000 responses | ≤ 1 per 1,000 | hallucination_incidents |
| AI positive feedback rate | M-20 | POSITIVE feedback / (POSITIVE + NEGATIVE) × 100 | ≥ 80% | ai_chat_messages.user_feedback |
| Corrective action plan (CAP) adoption rate | M-21 | CAP artifacts created / total CRITICAL findings assigned | ≥ 50% | ai_artifacts |
| Regulatory citation accuracy | M-22 | QA Officer-confirmed accurate citations / total citations sampled | ≥ 90% (manual sample of 50) | Manual review |

### 3.5 Security

| Metric | ID | Formula | Benchmark | Source |
|--------|-----|---------|-----------|--------|
| Cross-tenant access attempts | M-23 | Count of 403/404 responses from cross-institution requests | 0 successful cross-tenant accesses | audit logs |
| Failed login attempts | M-24 | Failed logins per day | Monitor for spikes (> 10 failed attempts per user per hour triggers alert) | auth_events |
| Rate limit triggers | M-25 | Count of 429 responses | Baseline; alert if sustained > 100/hour | Prometheus |

---

## 4. Qualitative Measures

### 4.1 Exit Survey (All Pilot Users)

Administered at end of 30-day pilot. 10-question Likert scale (1–5) + 3 open-text questions.

**Likert questions:**
1. I can find what I need to do my QA work without training or external assistance
2. The AI Workspace gives me accurate information about regulatory requirements
3. I trust the AI citations to be correct
4. The system helps me manage my quality assurance workload effectively
5. The compliance dashboard gives me a clear picture of my institution's QA status
6. I would recommend AQAA to a colleague in a similar role
7. The system is responsive and does not feel slow
8. I am confident that my institution's data is secure in this system
9. The finding and corrective action workflow reflects how QA work actually happens
10. Using AQAA has changed how I approach quality assurance in my role

**Open-text questions:**
1. What is the single most valuable thing AQAA has done for you during the pilot?
2. What is the most significant issue, gap, or frustration you experienced?
3. What feature would you most like to see added before commercial launch?

### 4.2 Role-Specific Qualitative Evaluation

**QA Officer interview (45 min, structured):**
- Walk me through how you would use AQAA to prepare for a CHE site visit
- Show me the last finding you worked on — how did the workflow compare to your previous process?
- What regulatory documents do you most frequently reference? Were they available in the system?

**Lecturer interview (30 min):**
- How did you know what evidence to upload for your module?
- Did the AI give you helpful guidance about what was needed?
- Was there anything confusing or missing in the module evidence checklist?

**Head of Department interview (30 min):**
- How useful was the department compliance dashboard in your daily work?
- How did you track corrective actions across your programme coordinators?

### 4.3 Session Observation

- 2 structured observation sessions with QA Officers during the pilot (shadowing via screenshare)
- Observer records: task completion time, error occurrences, help-seeking behaviour, confusion indicators
- Output: usability findings report (separate from evaluation plan metrics)

---

## 5. AI Quality Sampling Protocol

### 5.1 Weekly AI Output Sample

During the pilot, AQAA Engineering conducts a weekly manual sample of AI responses:
- Sample size: 20 responses per week (selected randomly from ai_audit_logs)
- Evaluation criteria:
  - Is the response factually accurate? (Yes / No / Uncertain)
  - Are the cited regulatory sources applicable to the query? (Yes / Partially / No)
  - Is the source_status correctly represented in the response? (Yes / No)
  - Does the response contain any PII or sensitive data it should not? (Yes / No)

### 5.2 Regulatory Citation Accuracy Check

At pilot end:
- Random sample of 50 citations from ai_audit_logs where `source_status = OFFICIAL_VERIFIED`
- Each citation manually verified against the source document
- Pass/fail recorded
- Target: ≥ 90% pass rate (metric M-22)

---

## 6. Pilot Phase Timeline

| Week | Evaluation Activity |
|------|-------------------|
| Week 1 | Onboarding observation; baseline engagement metrics captured |
| Week 2 | First AI output sample review; weekly DAU/session counts |
| Week 3 | Mid-pilot check-in with institution contact; corrective action completion check |
| Week 4 | Final week; exit survey administered on day 28; final observation session |
| Week 5 (post-pilot) | Survey analysis; interview synthesis; metrics report; lessons-learned document |

---

## 7. Success Thresholds

### Pilot Pass (proceed to commercial launch planning)

All of the following must be met:
- M-01 (uptime) ≥ 99.5%
- M-16 (grounding coverage) ≥ 85%
- M-19 (confirmed hallucination rate) ≤ 1 per 1,000
- M-20 (positive feedback rate) ≥ 80%
- M-22 (citation accuracy) ≥ 90%
- Exit survey Q6 (would recommend) average ≥ 4.0/5.0
- 0 critical security incidents (M-23)
- Exit survey open-text: no category of critical gap mentioned by > 50% of respondents

### Pilot Conditional Pass (proceed with mandatory remediation)

Between 5 and 8 metrics at threshold; no critical failures in security or AI accuracy; remediation backlog defined and committed before commercial launch planning begins.

### Pilot Fail (halt; reassess before re-pilot)

Any of:
- M-19 (confirmed hallucination rate) > 5 per 1,000
- M-01 (uptime) < 95%
- Any confirmed cross-tenant data access (M-23 > 0 successful)
- Exit survey Q6 average < 3.0/5.0
- Open-text reveals a fundamental workflow mismatch affecting > 50% of respondents

---

## 8. Output Documents

| Document | Produced By | Due |
|----------|------------|-----|
| Weekly metrics report | AQAA Engineering | Every Friday during pilot |
| AI output sample log | AQAA Engineering | Every Wednesday during pilot |
| Usability findings report | AQAA Engineering | Week 5 |
| Exit survey analysis | AQAA Engineering | Week 5 |
| Pilot evaluation summary | AQAA Engineering | Week 5 |
| Lessons-learned document | AQAA Engineering | Week 5 |
| Phase E completion report | AQAA Engineering | After all exit criteria met |

---

## Referenced Documents

- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md) — EVAL-* requirements
- [AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md](AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md)
- [AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md](AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md)
