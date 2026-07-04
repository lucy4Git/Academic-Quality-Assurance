# AQAA Use Case Diagram — Reference Guide

This document explains the actors and use cases depicted in
[`AQAA_Use_Case_Diagram.puml`](./AQAA_Use_Case_Diagram.puml). It is a companion
reference for developers, reviewers, and stakeholders who need a plain-language
description of what each symbol in the diagram represents.

The diagram models the **Academic Quality Assurance Agent (AQAA)** — a
standalone, multi-tenant, RBAC-secured platform for auditing the academic
quality of teaching modules across institutions, faculties, departments, and
programmes.

---

## 1. Actors

| Actor | Description |
|---|---|
| **Lecturer** | Module-level teaching staff. Uploads module evidence (lecture materials, attendance registers, assessments, moderation forms, etc.) and can view/trigger compliance audits and view QA reports for their own modules. |
| **Programme Coordinator** | Owns one or more programmes. Manages module records, triggers all compliance audit agents for modules in their programme, resolves audit findings, and views programme-level dashboards. |
| **Head of Department (HOD)** | Oversees all programmes within a department. Manages department and programme records and views department/programme dashboards and QA reports. |
| **Faculty Dean** | Oversees all departments within a faculty. Manages faculty records and views faculty/department dashboards and QA reports. |
| **Quality Assurance Officer (QA)** | Institution-wide QA role. Can run any compliance audit agent, generate findings/scores/reports across the institution, view audit logs, and review accreditation evidence packs. |
| **System Administrator (Admin)** | Highest privilege role. Manages the institution hierarchy (institutions, faculties, departments, programmes, modules), users, roles, RBAC permissions, and global audit logs. |
| **Student** | Read-only consumer. Can authenticate, manage their own profile, upload personal evidence (e.g. attendance/participation evidence where applicable), and view module compliance status. |
| **External Moderator** | An external examiner/moderator invited to review moderation evidence for specific modules and contribute to the Moderation Compliance Audit and QA reporting. |
| **Accreditation Body** | An external accreditation reviewer who runs/reviews the Accreditation Readiness Audit and inspects the accreditation evidence pack. |

> **Role hierarchy note:** Per `app/dependencies.py`, RBAC roles form a
> hierarchy where higher roles inherit the permissions of every role below
> them: `SYSTEM_ADMIN → QUALITY_ASSURANCE_OFFICER → FACULTY_DEAN →
> HEAD_OF_DEPARTMENT → PROGRAMME_COORDINATOR → LECTURER → STUDENT`. The
> diagram shows each actor's *additional* responsibilities at their level;
> in practice a higher role can also perform everything listed for the roles
> beneath it.

---

## 2. Use Cases

### 2.1 Authentication & Profile

| Use Case | Description |
|---|---|
| **Login / Authenticate** (UC1) | All actors authenticate via the auth service to obtain access/refresh tokens scoped to their institution and role. |
| **Manage Profile** (UC2) | View and update personal account details. |

### 2.2 Document & Evidence Management (Stage 6)

| Use Case | Description |
|---|---|
| **Upload Module Documents** (UC3) | Lecturers upload module folder documents (syllabi, assessments, attendance registers, moderation forms, LMS exports, etc.), which are categorized and queued for text extraction. |
| **Upload Evidence Files** (UC4) | Lecturers and students upload supporting evidence files associated with a module. |
| **View Module Compliance** (UC5) | View the current compliance status/scores for a module, drawn from the latest completed audit runs. |
| **Resolve Audit Findings** (UC6) | Mark individual audit findings as resolved with an optional note, preserving the audit trail. |

### 2.3 Institution & Academic Structure Management

| Use Case | Description |
|---|---|
| **Manage Institution Structure** (UC7) | Create/configure tenant institutions (multi-tenancy root). |
| **Manage Faculties** (UC8) | CRUD operations on faculties within an institution. |
| **Manage Departments** (UC9) | CRUD operations on departments within a faculty. |
| **Manage Programmes** (UC10) | CRUD operations on programmes within a department. |
| **Manage Modules** (UC11) | CRUD operations on modules within a programme. |

### 2.4 Compliance Audit Agents

| Use Case | Description |
|---|---|
| **Run Module Folder Audit** (UC12) | *(Stage 7)* Verifies the presence and structure of required module folder documents. |
| **Run Assessment Compliance Audit** (UC13) | *(Stage 8)* Verifies assessment design, coverage, and quality evidence (e.g. assessment briefs, marking rubrics, moderation of assessments). |
| **Run Moderation Compliance Audit** (UC14) | *(Stage 9)* Verifies internal/external moderation evidence — moderation forms, sign-offs, sample selection, date sequencing. |
| **Run Attendance Compliance Audit** (UC15) | *(Stage 10)* Verifies attendance evidence for lectures, tutorials, practicals/labs, and LMS participation, including weekly coverage completeness and risk level. |
| **Run Evidence Verification Audit** (UC16) | *(Planned)* Cross-checks that evidence referenced by other agents is genuinely present, authentic, and traceable to its source documents. |
| **Run Outcome Alignment Audit** (UC17) | *(Planned)* Verifies that module/programme learning outcomes are aligned with assessments, content, and accreditation requirements. |
| **Run Accreditation Readiness Audit** (UC18) | *(Planned)* Aggregates findings across all other agents to assess overall readiness for an accreditation review. |

### 2.5 Shared Audit Pipeline (used by all agents via `<<includes>>`)

| Use Case | Description |
|---|---|
| **Extract and Classify Documents** (UC19) | *(Stage 6)* Shared document-processing step: extracts text from uploaded files and classifies them by category so audit agents can probe their content. |
| **Generate Audit Findings** (UC20) | *(Stage 7+)* Shared findings engine: each agent's checklist/probe failures are written as `AuditFinding` rows with severity, type, and recommendations. |
| **Calculate Compliance Score** (UC21) | Shared two-component scoring (`scoring_common.py`): `overall_score = presence_score × 0.60 + quality_score × 0.40`, mapped to an `AuditStatus`. |
| **Generate QA Reports** (UC22) | Produces the structured per-run compliance report (scores, status, findings, breakdowns) consumed by all roles. |

### 2.6 Dashboards

| Use Case | Description |
|---|---|
| **View Programme Dashboard** (UC23) | Aggregated compliance view across all modules in a programme. |
| **View Department Dashboard** (UC24) | Aggregated compliance view across all programmes in a department. |
| **View Faculty Dashboard** (UC25) | Aggregated compliance view across all departments in a faculty. |
| **View Institutional Dashboard** (UC26) | Institution-wide aggregated compliance view (QA Officer level). |

### 2.7 Administration & Governance

| Use Case | Description |
|---|---|
| **Configure QA Rules** (UC27) | Admin-level configuration of audit checklists, thresholds, and scoring parameters. |
| **Manage Users and Roles** (UC28) | Create/deactivate user accounts and assign RBAC roles. |
| **Manage RBAC Permissions** (UC29) | Configure which roles can access which actions/resources. |
| **View Audit Logs** (UC30) | View system-wide audit run history and activity logs for governance/oversight. |

### 2.8 External Review

| Use Case | Description |
|---|---|
| **Review Moderation Evidence** (UC31) | External moderators review moderation documentation and sign-offs as part of the Moderation Compliance Audit. |
| **Review Accreditation Evidence Pack** (UC32) | Accreditation bodies and QA Officers review the consolidated evidence pack produced for accreditation readiness. |

---

## 3. Relationships

- All seven compliance audit use cases (UC12–UC18) **include** the shared
  document extraction/classification step (UC19), since every agent operates
  on processed module folder documents.
- All seven compliance audit use cases **include** the shared findings
  engine (UC20), since every agent persists its results as `AuditFinding`
  rows.
- The findings engine (UC20) **includes** the shared scoring engine (UC21),
  since findings drive the presence/quality score calculation.
- The scoring engine (UC21) **includes** report generation (UC22), since a
  compliance score is always surfaced as part of a structured report.

---

## 4. Implementation Status

| Audit Agent | Status | Stage |
|---|---|---|
| Module Folder Audit | ✅ Implemented | Stage 7 |
| Assessment Compliance Audit | ✅ Implemented | Stage 8 |
| Moderation Compliance Audit | ✅ Implemented | Stage 9 |
| Attendance Compliance Audit | ✅ Implemented | Stage 10 |
| Evidence Verification Audit | 🔜 Planned | Future stage |
| Outcome Alignment Audit | 🔜 Planned | Future stage |
| Accreditation Readiness Audit | 🔜 Planned | Future stage |

The diagram intentionally includes the three planned agents (per
`CLAUDE.md`'s documented AI Agent list) so the use case model represents the
full target architecture, not just the current implementation snapshot.
