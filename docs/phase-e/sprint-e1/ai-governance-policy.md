# AQAA AI Governance Policy
**Document ID**: E1-GOV-001  
**Effective Date**: 2026-07-24  
**Review Cycle**: Annual

---

## 1. Purpose

This policy governs the use of AI-assisted features within the Academic Quality
Assurance Agent (AQAA) platform. It defines transparency obligations, data
handling constraints, human oversight requirements, and acceptable use
boundaries for all AI-generated outputs.

## 2. Scope

Applies to all AQAA users — QA officers, faculty deans, heads of department,
programme coordinators, and lecturers — accessing AI-assisted audit analysis,
knowledge extraction, or the AI Workspace feature.

## 3. AI Assistance Transparency (E1-GOV-002)

**All AI-generated content displayed to users carries an "AI-assisted" label.**
This label is rendered in the AQAA UI adjacent to any content produced or
summarised by a language model, vector-search retrieval result, or AI audit
finding. Users must not be misled into believing AI output has been produced
by a human reviewer.

## 4. Human Oversight Requirement

AI audit findings are **advisory only**. Every audit finding, corrective action
recommendation, and accreditation readiness assessment produced by AQAA:

- Must be reviewed and accepted or rejected by an authorised human (QA officer
  or higher).
- Does not constitute a formal institutional decision until confirmed by an
  authorised person.
- Must not be submitted to an external accreditation body without human review.

## 5. Data Sent to External AI Providers

AQAA uses external AI providers (e.g. Anthropic, OpenAI) for language model
inference. The following constraints apply:

- **No personally identifiable information (PII)** about students, staff, or
  third parties is sent to AI providers unless it is directly necessary for the
  analysis and the user has been informed.
- **No raw authentication credentials, access tokens, or passwords** are ever
  included in AI prompts.
- Sentry error tracking (`send_default_pii=False`) does not transmit prompts,
  document content, or personal information.
- Institution-specific policy documents and evidence files are sent to AI
  providers only for the purpose of generating audit analysis. They are not
  used by providers to train models (per provider data processing agreements).

## 6. Data Governance (OD-01, OD-02 — OPEN)

The following decisions remain open and must be resolved before processing real
institutional or personal data:

- **OD-01**: Data governance agreement between AQAA and pilot institutions.
- **OD-02**: Consent framework for AI-assisted processing of student and staff
  records.

No real institutional or personal data may be used in AQAA until OD-01 and
OD-02 are formally resolved.

## 7. Audit Trail

All AI audit runs are logged with:
- Timestamp, user ID, institution ID, module/programme scope
- AI agent type and version
- Run status and finding count
- Background job log entry (Sprint E1 `background_job_logs` table)

Audit logs are retained for a minimum of 7 years.

## 8. Prohibited Uses

AI features in AQAA must not be used to:
- Make automated decisions about individual students' academic standing
  without human oversight.
- Generate content that could be submitted as official institutional policy
  without human authorship and review.
- Bypass accreditation body requirements for human-authored documentation.

## 9. Complaints and Review

Users who believe an AI-generated finding is inaccurate or harmful may raise a
corrective action (via the AQAA Corrective Actions module) or contact their
institution's QA officer. AQAA Engineering reviews reported AI quality issues
within 10 working days.

---

*This policy is subject to annual review and may be updated to reflect changes
in AI provider terms, regulatory requirements, or operational experience.*
