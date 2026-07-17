# AQAA Phase E — Data Requirements

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. New Data Models

Phase E introduces **9 new database tables** in total:

| # | Table | Sprint | Purpose |
|---|-------|--------|---------|
| 1 | corrective_actions | E1 | Structured corrective action records |
| 2 | corrective_action_history | E1 | Append-only state-change history |
| 3 | ai_audit_logs | E2 | All AI completion events (governance) |
| 4 | hallucination_incidents | E2 | Confirmed hallucination records |
| 5 | regulatory_document_registry | E2 | CHE/DHET/SAQA document metadata |
| 6 | compliance_trend_snapshots | E3 | Pre-aggregated analytics (read-optimised) |
| 7 | pilot_consent | E5 | Pilot participant consent records |
| 8 | background_job_logs | E0 | ARQ job execution audit log |
| 9 | audit_trigger_schedules | E1 | Scheduled audit configurations |

Additionally, two existing tables receive new columns (M-E-06, M-E-07): `ai_chat_messages.user_feedback` and `findings.primary_corrective_action_id`. These are column additions, not new tables.

---

### 1.1 CorrectiveAction

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| finding_id | UUID FK → findings | NOT NULL |
| created_by | UUID FK → users | NOT NULL |
| assigned_to | UUID FK → users | NULL = unassigned |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| due_date | DATE | NULL = no deadline |
| status | ENUM | OPEN, IN_PROGRESS, OVERDUE, RESOLUTION_SUBMITTED, CLOSED |
| evidence_of_resolution | TEXT | URL or description of evidence |
| closed_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### 1.2 CorrectiveActionHistory (append-only)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| corrective_action_id | UUID FK | NOT NULL |
| from_status | VARCHAR(50) | NULL on creation |
| to_status | VARCHAR(50) | NOT NULL |
| changed_by | UUID FK → users | NOT NULL |
| note | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 1.3 AiAuditLog (append-only)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| session_id | UUID FK → ai_chat_sessions | NOT NULL |
| message_id | UUID FK → ai_chat_messages | NOT NULL |
| institution_id | UUID FK → institutions | NOT NULL |
| user_id | UUID FK → users | NOT NULL |
| query_hash | VARCHAR(64) | SHA-256 of query text |
| response_hash | VARCHAR(64) | SHA-256 of response text |
| sources_cited | JSONB | Array of {source_id, source_status, doc_name} |
| grounding_coverage | FLOAT | 0.0–1.0; NULL if no sources cited |
| model_provider | VARCHAR(50) | |
| model_name | VARCHAR(100) | |
| tokens_prompt | INTEGER | |
| tokens_completion | INTEGER | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 1.4 HallucinationIncident

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| audit_log_id | UUID FK → ai_audit_logs | NOT NULL |
| flagged_by | UUID FK → users | NOT NULL |
| reason | TEXT | NOT NULL |
| status | VARCHAR(50) | OPEN, REVIEWED, DISMISSED, CONFIRMED |
| reviewed_by | UUID FK → users | NULL until reviewed |
| reviewed_at | TIMESTAMPTZ | |
| resolution_note | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 1.5 RegulatoryDocumentRegistry

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| title | VARCHAR(255) | NOT NULL |
| issuing_body | VARCHAR(100) | e.g. CHE, DHET, SAQA |
| document_version | VARCHAR(50) | |
| effective_date | DATE | |
| source_url | TEXT | Public URL of source document |
| source_status | VARCHAR(50) | OFFICIAL_VERIFIED, INSTITUTIONAL_APPROVED, TEST_FIXTURE, DRAFT_IMPORT, SUPERSEDED |
| institution_id | UUID FK | NULL = national/cross-institution |
| qdrant_collection | VARCHAR(100) | Collection in which document is indexed |
| point_ids | JSONB | Array of Qdrant point UUIDs |
| ingested_at | TIMESTAMPTZ | |
| ingested_by | UUID FK → users | |
| superseded_by | UUID FK → self | NULL unless superseded |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 1.6 ComplianceTrendSnapshot

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| institution_id | UUID FK | NOT NULL |
| faculty_id | UUID FK | NULL = institution-level |
| department_id | UUID FK | NULL |
| programme_id | UUID FK | NULL |
| period_start | DATE | Start of aggregation window |
| period_end | DATE | End of aggregation window |
| audit_count | INTEGER | |
| completed_count | INTEGER | |
| critical_count | INTEGER | |
| avg_score_percentage | FLOAT | |
| finding_severity_breakdown | JSONB | {CRITICAL: N, HIGH: N, MEDIUM: N, LOW: N} |
| computed_at | TIMESTAMPTZ | DEFAULT now() |

### 1.7 PilotConsent

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| institution_id | UUID FK | NOT NULL |
| signatory_name | VARCHAR(255) | NOT NULL |
| signatory_role | VARCHAR(100) | NOT NULL |
| signatory_email | VARCHAR(255) | NOT NULL |
| consent_date | DATE | NOT NULL |
| data_processing_scope | TEXT | Description of what data will be processed |
| retention_period_agreed | VARCHAR(100) | e.g. "7 years per schedule" |
| popia_acknowledged | BOOLEAN | NOT NULL DEFAULT FALSE |
| nda_signed | BOOLEAN | NOT NULL DEFAULT FALSE |
| pilot_start_date | DATE | |
| pilot_end_date | DATE | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 1.8 Additions to Existing Tables

| Table | New Column | Type | Notes |
|-------|-----------|------|-------|
| ai_chat_messages | user_feedback | VARCHAR(20) | NULL, POSITIVE, NEGATIVE |
| findings | primary_corrective_action_id | UUID FK | NULL; links to corrective_actions |
| users | mfa_enabled | BOOLEAN | DEFAULT FALSE |
| users | mfa_secret | VARCHAR(255) | Encrypted TOTP secret; NULL if not enrolled |
| users | deleted_at | TIMESTAMPTZ | Soft delete |

---

## 2. Data for Autonomous Monitoring

### 2.1 Scheduler State

The ARQ worker requires no new database table — it uses Redis for job queue and scheduling state. However, a lightweight job execution log is needed for audit and debugging:

**New table: background_job_logs**

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| job_name | VARCHAR(100) | Task function name |
| job_args | JSONB | Serialised arguments |
| status | VARCHAR(50) | QUEUED, RUNNING, COMPLETED, FAILED, RETRYING |
| attempt_number | INTEGER | 1–4 (1 initial + 3 retries) |
| institution_id | UUID FK | NULL for system-wide jobs |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| error_message | TEXT | NULL on success |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 2.2 Audit Trigger Schedule

**New table: audit_trigger_schedules**

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| institution_id | UUID FK | NOT NULL |
| scope | VARCHAR(50) | INSTITUTION, FACULTY, DEPARTMENT, PROGRAMME, MODULE |
| scope_id | UUID | Relevant entity UUID |
| agent_type | VARCHAR(100) | Maps to AgentType enum |
| frequency | VARCHAR(50) | DAILY, WEEKLY, MONTHLY, ONCE |
| next_run_at | TIMESTAMPTZ | Computed by scheduler |
| last_run_at | TIMESTAMPTZ | |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_by | UUID FK → users | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## 3. Data for Pilot

### 3.1 Pilot Seed Requirements

Before onboarding the first pilot institution:
- All existing seed data (GFU, RCT) must be clearly marked as `TEST_INSTITUTION = TRUE` or separated from production data
- Pilot institution data must use a distinct institution record with real organisational structure
- No fictional student identifiers may conflict with real student number formats
- Pilot users must have clearly fictional email addresses (`*.pilot.aqaa.za`) during the trial period

### 3.2 Pilot Data Isolation Strategy

During the pilot, production data (real institutional records) must be isolated from AQAA Engineering's internal test data:
- Separate institution records per tenant (existing multi-tenant model handles this)
- Separate Qdrant namespaces per institution (existing `institution_id` filter handles this)
- AQAA Engineering test institution (`institution_id = RESERVED_TEST_UUID`) must never appear in pilot reports

### 3.3 Data Migration for Pilot Go-Live

On pilot go-live day:
1. Apply all Phase E migrations (`alembic upgrade head`)
2. Ingest OFFICIAL_VERIFIED regulatory documents into Qdrant
3. Create pilot institution record via tenant provisioning API
4. Create pilot users via admin panel
5. Record `PilotConsent` entry
6. Verify database backup is current
7. Verify Qdrant snapshot is current

---

## 4. Analytics Data Requirements

### 4.1 Compliance Trend Data

Source queries for trend aggregation job:

```sql
-- Weekly compliance score per programme
SELECT
    ar.programme_id,
    m.institution_id,
    m.faculty_id,
    m.department_id,
    DATE_TRUNC('week', ar.created_at) AS period_start,
    DATE_TRUNC('week', ar.created_at) + INTERVAL '6 days' AS period_end,
    AVG(ar.score_percentage) AS avg_score,
    COUNT(*) AS audit_count,
    COUNT(*) FILTER (WHERE ar.overall_status = 'CRITICAL') AS critical_count,
    COUNT(f.id) FILTER (WHERE f.severity = 'CRITICAL' AND f.status != 'CLOSED') AS open_critical_findings
FROM audit_runs ar
LEFT JOIN modules m ON ar.module_id = m.id
LEFT JOIN findings f ON f.audit_run_id = ar.id
WHERE ar.run_status = 'completed'
  AND ar.created_at >= NOW() - INTERVAL '12 months'
GROUP BY ar.programme_id, m.institution_id, m.faculty_id, m.department_id,
         DATE_TRUNC('week', ar.created_at)
```

Results cached in `compliance_trend_snapshots` and Redis (TTL 3600s).

### 4.2 Heat Map Data

Source for faculty heat map:

```sql
SELECT
    f.id AS faculty_id,
    f.name AS faculty_name,
    AVG(cts.avg_score_percentage) AS avg_compliance_score,
    SUM(cts.critical_count) AS total_critical_count,
    SUM(cts.audit_count) AS total_audits,
    MAX(cts.period_end) AS latest_period
FROM compliance_trend_snapshots cts
JOIN faculties f ON cts.faculty_id = f.id
WHERE cts.institution_id = :institution_id
  AND cts.period_start >= NOW() - INTERVAL '90 days'
GROUP BY f.id, f.name
ORDER BY avg_compliance_score ASC
```

### 4.3 Evaluation Data Points

The following data points must be logged and accessible for evaluation against the metrics in the Evaluation Plan:

| Data Point | Source |
|-----------|--------|
| Session count per user per week | ai_chat_sessions |
| Audit trigger count (manual vs automated) | audit_runs + background_job_logs |
| Time from finding to resolution | findings (created_at → closed_at) |
| Corrective action completion rate | corrective_actions |
| AI grounding coverage trend | ai_audit_logs |
| User feedback ratio (positive/negative) | ai_chat_messages.user_feedback |
| System response time per endpoint | Prometheus metrics |
| Hallucination incident rate | hallucination_incidents / ai_audit_logs |

---

## 5. Data Quality Rules

| Rule | Enforcement |
|------|------------|
| No student personal identifiers in AI prompts | Prompt sanitisation function in `ai_assistant/prompt_templates.py` |
| `grounding_coverage` must be between 0.0 and 1.0 | Database CHECK constraint |
| `AiAuditLog` rows are never updated or deleted | No UPDATE/DELETE routes; DB trigger to enforce |
| `CorrectiveActionHistory` rows are never updated or deleted | Same as above |
| `source_status` transitions follow the allowed state machine | Service-layer validation |
| Pilot consent must be recorded before institution goes live | Checked in tenant provisioning API |

---

## Referenced Documents

- [AQAA_PHASE_E_ARCHITECTURE_PLAN.md](AQAA_PHASE_E_ARCHITECTURE_PLAN.md) — Migration plan, model diagrams
- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md) — DATA-* requirements
- [AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md](AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md) — Retention schedule
