# AQAA Phase E — Security and Governance Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Regulatory Context

AQAA operates in the South African Higher Education sector. The following legislation and regulations apply:

| Legislation | Relevance |
|-------------|-----------|
| Protection of Personal Information Act (POPIA) No. 4 of 2013 | Processing of student, staff, and institutional personal information |
| Higher Education Act No. 101 of 1997 | Institutional data and quality assurance obligations |
| NQF Act No. 67 of 2008 | Qualification records and accreditation data |
| Electronic Communications and Transactions Act (ECTA) No. 25 of 2002 | Electronic records, signatures, and data security |
| Constitution of South Africa, Section 14 | Right to privacy |

---

## 2. POPIA Compliance Plan

### 2.1 Data Protection Impact Assessment (DPIA)

A DPIA is required before the pilot because AQAA:
- Processes personal information of students, lecturers, QA officers, and administrators
- Uses AI to analyse and generate findings related to academic staff performance
- Stores uploaded documents that may contain personal records

**DPIA scope:**
1. Identify all personal information processed (categories, subjects, volume)
2. Document lawful basis for processing per POPIA s.11
3. Assess proportionality and necessity
4. Identify risks to data subjects
5. Specify technical and organisational mitigations
6. Record institutional Information Officer sign-off

**Responsible party:** The institution deploying AQAA is the Responsible Party under POPIA. AQAA Engineering is the Operator. A written Data Processing Agreement (DPA) is required before pilot deployment.

### 2.2 Data Subject Rights

| Right | Implementation Required |
|-------|------------------------|
| Right of access (s.23) | DSAR export: JSON of all personal data for named user, downloadable by System Admin |
| Right to correction (s.24) | Admin user edit panel (existing) |
| Right to deletion (s.27) | Soft-delete users; hard-delete on DSAR + retention expiry |
| Right to object to processing (s.11(3)) | Opt-out flag for AI analysis; documented procedure |
| Right not to be subject to automated decision making (s.71) | AI findings labelled "AI-assisted, requires human review" |

### 2.3 Data Retention Schedule

| Data Category | Retention Period | Disposal Method |
|--------------|-----------------|----------------|
| User account records | Duration of employment + 5 years | Hard delete + audit log |
| Audit run records | 7 years | Archive then delete |
| AI conversation records | 5 years | Archive then delete |
| AI audit logs | 5 years (regulatory minimum) | Append-only; archive at expiry |
| Uploaded evidence files | 7 years or per institutional policy | Secure deletion |
| Pilot consent records | Duration of agreement + 5 years | Retain as legal record |
| Authentication logs | 3 years | Archive then delete |

### 2.4 Third-Party Data Sharing

**AI Provider:** Queries sent to AI providers (Anthropic, OpenAI) may contain user-inputted text and excerpts from uploaded documents. The following controls apply:
- No student personal identifiers (name, student number) shall be included in AI prompts. A prompt sanitisation check shall strip identifiable patterns before submission.
- Data Processing Agreements with AI providers must be in place before pilot.
- AI providers' data residency and retention policies must be documented and disclosed to institutions.

---

## 3. Threat Model

### 3.1 Assets

| Asset | Sensitivity |
|-------|------------|
| User credentials | CRITICAL |
| JWT access tokens | CRITICAL |
| AI provider API keys | CRITICAL |
| Student academic records in uploaded files | HIGH |
| Audit findings and corrective action records | HIGH |
| AI conversation history | HIGH |
| Regulatory knowledge base | MEDIUM |
| Aggregate analytics data | LOW |

### 3.2 Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|-----------|
| External attacker (internet) | Medium | Credential theft, data exfiltration |
| Malicious tenant user | Low-Medium | Cross-tenant data access, privilege escalation |
| Compromised service account | Medium | Internal data access, AI key theft |
| Supply chain attacker | High | Backdoored dependency |

### 3.3 STRIDE Analysis

| Threat | Control |
|--------|---------|
| **Spoofing** — JWT impersonation | Short-lived tokens (60 min), deny-list on logout, MFA for elevated roles |
| **Tampering** — API request manipulation | Input validation (Pydantic), server-side MIME check, parameterised queries |
| **Repudiation** — denied actions | Immutable audit log, authentication event logging |
| **Information Disclosure** — cross-tenant data | Row-level institution_id filter, 404 not 403 for cross-tenant resources |
| **Denial of Service** — API abuse | Rate limiting (200 req/min authenticated, 30 req/min unauthenticated) |
| **Elevation of Privilege** — role bypass | Route-level RBAC via FastAPI Depends, no client-trusted role claims |

### 3.4 Attack Vectors — Mitigation Map

| Attack Vector | Mitigation |
|--------------|-----------|
| SQL injection | SQLAlchemy ORM with parameterised binds; no raw SQL with string formatting |
| XSS | React JSX escaping; CSP headers via reverse proxy |
| CSRF | SameSite=Strict on session cookies; no state-changing GET endpoints |
| File upload attacks | Server-side MIME validation; ClamAV scan; size limit; no execution of uploaded files |
| Prompt injection via uploaded documents | Content sanitisation before AI prompt injection; source labelling |
| Dependency supply chain | `pip audit` and `npm audit` in CI; pinned versions in requirements.txt and package-lock.json |
| Secrets in git | Pre-commit hook: block `.env` files; secret pattern scanner in CI |

---

## 4. Security Controls — Implementation Plan

### 4.1 Authentication and Session Management

| Control | Implementation | Sprint |
|---------|---------------|--------|
| Rate limiting | `slowapi` (FastAPI limiter) on all routes | E0 |
| JWT deny-list on logout | Redis SET with token `jti`, TTL = token expiry | E0 |
| MFA (TOTP) | `pyotp` library; QR code provisioning for QA_OFFICER+ | E1 |
| Session cookie hardening | `SameSite=Strict; Secure; HttpOnly` — already set; verify in prod config | E0 |
| Concurrent session limit | Redis counter per user; reject new login if > N active sessions | E2 |

### 4.2 API Security

| Control | Implementation | Sprint |
|---------|---------------|--------|
| Rate limiting | `slowapi` with Redis backend | E0 |
| Input validation | Pydantic v2 models (already in use) | Existing |
| CORS origin whitelist | `CORS_ORIGINS` env var; no wildcard in production | E0 |
| Security headers | Caddy/nginx config: CSP, HSTS, X-Frame-Options, X-Content-Type-Options | E0 |
| HTTPS everywhere | TLS via Caddy automatic certificate | E0 |

### 4.3 Data Security

| Control | Implementation | Sprint |
|---------|---------------|--------|
| Storage path tenant namespacing | `uploads/{institution_id}/{category}/{file_id}` | E1 |
| Virus scanning | ClamAV via `clamd` socket; `VIRUS_SCAN_ENABLED=True` default in prod | E1 |
| Server-side MIME validation | `python-magic` library; reject if MIME ≠ declared extension | E1 |
| Backup encryption | pg_dump piped through `gpg --symmetric` before storage | E2 |

### 4.4 Secrets Management

**Phase E approach: mounted secrets file (no Vault in pilot, Vault in Phase F)**

```
Production deployment:
    docker-compose.prod.yml
    secrets:
      secret_key:
        file: ./secrets/secret_key.txt
      database_url:
        file: ./secrets/database_url.txt
      ...

    services:
      backend:
        secrets: [secret_key, database_url, ...]
        environment:
          SECRET_KEY_FILE: /run/secrets/secret_key
          DATABASE_URL_FILE: /run/secrets/database_url

Config.py reads:
    import os
    def read_secret(env_var: str) -> str:
        file_path = os.environ.get(f"{env_var}_FILE")
        if file_path and os.path.exists(file_path):
            return open(file_path).read().strip()
        return os.environ[env_var]
```

---

## 5. AI Governance Framework

### 5.1 Governance Principles

1. **Transparency**: All AI-generated content is labelled. Users always know when they are reading AI output.
2. **Human oversight**: AI findings are advisory. No regulatory action shall be taken on AI output alone without human review.
3. **Grounding first**: AI responses shall cite verified sources. Responses with zero verified citations shall carry a visible warning.
4. **Accountability**: Every AI interaction is logged. Logs are immutable and retained for 5 years.
5. **Continuous improvement**: Hallucination incidents are reviewed weekly. Prompt templates are updated in response to confirmed incidents.

### 5.2 AI Output Classification

| Classification | Criteria | UI Treatment |
|---------------|---------|-------------|
| Grounded | ≥1 OFFICIAL_VERIFIED or INSTITUTIONAL_APPROVED source cited | Normal display |
| Partially grounded | Sources cited but none OFFICIAL_VERIFIED | Yellow badge: "Institutional sources only" |
| Ungrounded | No regulatory source cited | Orange badge: "No regulatory source — verify independently" |
| Speculative | Response includes explicit AI uncertainty language | Blue badge: "AI inference — not a regulatory determination" |

### 5.3 Hallucination Management

**Detection:** QA Officers flag suspected hallucinations via thumbs-down + "Report inaccuracy" button.

**Triage:** AQAA Engineering reviews flagged incidents within 5 business days.

**Resolution options:**
- DISMISSED: response was correct, user misunderstood
- CONFIRMED: response contained factual error; prompt template updated; affected institution notified
- NEEDS_MORE_INFO: follow-up with flagging user required

**Metrics:**
- Hallucination incident rate: incidents per 1,000 responses (target: < 5)
- Confirmed hallucination rate: confirmed incidents per 1,000 responses (target: < 1)

### 5.4 AI Provider Governance

| Control | Requirement |
|---------|------------|
| Data processing agreement | Required before pilot for all providers used |
| Data residency | Provider must confirm SA or EU/UK data residency; no US-only providers without DPA |
| Model versioning | Model version logged per response; version changes trigger a regression test run |
| Prompt template versioning | All templates version-controlled in `backend/app/ai_assistant/prompt_templates.py`; changes require code review |
| Provider failover | Primary + secondary provider configured; automatic failover on HTTP 5xx or timeout |
| Cost governance | Per-institution monthly AI token budget configurable; alert at 80%, hard cap at 100% |

### 5.5 Governance Policy Document

A human-readable `AI_GOVERNANCE_POLICY.md` must be created before pilot, covering:
- What data is sent to AI providers
- What is retained vs deleted
- How to report a concern
- Human review obligations
- Annual governance review schedule

Location: `docs/governance/AI_GOVERNANCE_POLICY.md`

---

## 6. Security Testing Plan

| Test | Tool | When |
|------|------|------|
| Dependency vulnerability scan | `pip audit`, `npm audit` | Every CI run |
| Static analysis | `bandit` (Python), `eslint-security` (TS) | Every CI run |
| OWASP Top 10 review | Manual checklist | Sprint E2 (pre-pilot) |
| Penetration test — authentication | Manual (internal) | Sprint E3 |
| Penetration test — cross-tenant isolation | Manual (internal) | Sprint E3 |
| File upload abuse test | Manual | Sprint E2 |
| Rate limiting verification | `locust` or `hey` | Sprint E2 |
| Secret scanning | `truffleHog` or `git-secrets` | CI pre-commit |

---

## 7. Incident Response Plan

### Classification

| Severity | Definition | Response Time |
|----------|-----------|--------------|
| P0 — Critical | Active breach, data exfiltration, system compromise | 1 hour |
| P1 — High | Suspected breach, privilege escalation, service down | 4 hours |
| P2 — Medium | Security misconfiguration detected, anomalous access | 24 hours |
| P3 — Low | Policy violation, non-critical vulnerability | 5 business days |

### Response Procedure

1. **Detect**: Sentry alert, log anomaly, user report, or monitoring alert
2. **Contain**: Isolate affected service; revoke compromised credentials
3. **Assess**: Determine scope, affected institutions, data subjects
4. **Notify**: POPIA requires notification to Information Regulator within 72 hours of a significant breach; affected data subjects notified without undue delay
5. **Remediate**: Apply fix; verify fix; resume services
6. **Review**: Post-incident report within 5 business days; update controls

---

## Referenced Documents

- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md) — SEC-*, GOV-* requirements
- [AQAA_PHASE_E_ARCHITECTURE_PLAN.md](AQAA_PHASE_E_ARCHITECTURE_PLAN.md) — Secrets management design
- `docs/governance/AI_GOVERNANCE_POLICY.md` — To be created in Sprint E2
