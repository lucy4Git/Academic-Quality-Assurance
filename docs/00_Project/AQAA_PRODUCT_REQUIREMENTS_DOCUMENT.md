# AQAA — Product Requirements Document

**Document ID:** PRD-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29  
**Owner:** AQAA Product & Engineering  
**Classification:** Internal — Product Reference

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision and Mission](#2-product-vision-and-mission)
3. [Product Goals](#3-product-goals)
4. [Problem Statement](#4-problem-statement)
5. [Stakeholders](#5-stakeholders)
6. [User Personas](#6-user-personas)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [AI Capabilities](#9-ai-capabilities)
10. [Institutional Knowledge Package](#10-institutional-knowledge-package)
11. [Qualification Intelligence](#11-qualification-intelligence)
12. [Reporting and Analytics](#12-reporting-and-analytics)
13. [Security and Governance](#13-security-and-governance)
14. [Success Metrics](#14-success-metrics)
15. [Product Roadmap](#15-product-roadmap)
16. [Risks](#16-risks)
17. [Constraints](#17-constraints)
18. [Future Enhancements](#18-future-enhancements)

---

## 1. Executive Summary

AQAA (Academic Quality Assurance Agent) is an enterprise-grade, AI-augmented platform that digitises, automates, and governs academic quality assurance for universities, universities of technology, TVET colleges, and accreditation agencies.

The platform addresses a critical operational gap in South African higher education: the QA audit cycle — verifying that every module folder contains the required documentation (learning outcomes, assessment briefs, moderation records, attendance registers, learner evidence) — is currently paper-based, manual, inconsistent, and severely under-resourced relative to the volume of modules that must be audited annually.

AQAA replaces this process with a governed digital system: structured evidence upload, AI-assisted gap detection, human-led compliance review, workflow automation, and a versioned institutional knowledge base. Every record is traceable to its authoritative source. Every compliance decision is made by a qualified human professional. Every finding is auditable.

The platform is built as a multi-tenant SaaS product capable of serving South Africa's 26 public universities, 50 TVET colleges, and future international clients from a single deployment, with complete data isolation between institutions.

**Pilot institution:** Tshwane University of Technology (TUT) — Faculty of Information and Communication Technology.

---

## 2. Product Vision and Mission

### 2.1 Vision

> **To become the definitive academic quality intelligence platform for higher education in Africa and beyond** — enabling every institution to achieve sustainable, evidence-driven quality through intelligent automation and transparent governance.

### 2.2 Mission

> Enable every academic institution to achieve and sustain compliance with national and international quality standards through an evidence-first, AI-assisted, human-governed platform that makes quality assurance accessible, consistent, and scalable.

### 2.3 Core Beliefs

| Belief | Implication for AQAA |
|--------|---------------------|
| Evidence proves quality | AQAA tracks evidence, not intent |
| Humans must decide compliance | AI generates findings; professionals approve them |
| Provenance builds trust | Every data point is traceable to its official source |
| Quality scales with technology | 300 modules can be audited as easily as 3 |
| Institutions own their data | Multi-tenant isolation is non-negotiable |

---

## 3. Product Goals

### 3.1 Primary Goals

| Goal | Measurable Target | Timeline |
|------|------------------|---------|
| Digitise module folder QA audit | 100% of module audits conducted digitally | Pilot phase |
| Reduce audit preparation time | 60% reduction in time to prepare audit evidence | 12 months post-pilot |
| Automate evidence gap detection | 8 AI agents cover all major document categories | ✅ Complete |
| Enable multi-institution deployment | Single platform serves ≥ 3 institutions | Phase 6 |
| Establish institutional knowledge base | IKP for every onboarded institution | Phase 6–8 |
| Support CHE accreditation cycles | Audit reports match CHE evidence requirements | Phase 6 |

### 3.2 Secondary Goals

- Reduce dependency on spreadsheet-based QA tracking
- Create an auditable digital record of all QA activities
- Provide trend analytics across academic years
- Enable proactive gap detection before accreditation visits

---

## 4. Problem Statement

### 4.1 The Core Problem

South African higher education institutions are required by the Council on Higher Education (CHE) and the Department of Higher Education and Training (DHET) to demonstrate continuous quality assurance across all academic programmes. At the module level, this means maintaining complete, up-to-date module folders containing specific document types for every taught module in every academic year.

For an institution with 300 modules, this represents 300 × 10 = 3,000 individual document checks per year. The current process is:

1. **Manual:** QA Officers physically or digitally check each folder
2. **Inconsistent:** No standardised checklist across programmes or faculties
3. **Undocumented:** No audit trail of who checked what and when
4. **Reactive:** Issues are discovered at review time, not prevented proactively
5. **Under-resourced:** QA teams cannot audit all modules annually at scale

### 4.2 Consequences of the Current State

| Consequence | Impact |
|------------|--------|
| Incomplete evidence folders | CHE non-compliance, risk of programme suspension |
| Undocumented QA activities | Cannot demonstrate quality improvement to accreditors |
| Inconsistent standards | Different faculties interpret requirements differently |
| Late detection | Problems discovered at accreditation time, not in-year |
| Audit fatigue | QA Officers spend most time on evidence hunting, not analysis |

### 4.3 What AQAA Solves

- **Structural:** Imposes consistent, institutional-specific QA structure via IKP
- **Operational:** Automates evidence gap detection across all modules
- **Governance:** Creates auditable digital trail for all QA activities
- **Analytical:** Enables trend analysis and proactive risk identification
- **Scalability:** Handles 300+ modules with the same effort as 30

---

## 5. Stakeholders

### 5.1 Internal Stakeholders (Within Each Institution)

| Stakeholder | Role in QA | Interest in AQAA |
|-------------|-----------|-----------------|
| Vice Chancellor / Rector | Institutional accountability for quality | Governance dashboard, compliance reports |
| Deputy VC: Academic | Oversees academic quality | Faculty-level compliance trends |
| Faculty Dean | Faculty quality compliance | Faculty audit status, finding summaries |
| Head of Department | Department-level evidence gathering | Department compliance scores |
| Programme Coordinator | Module folder compilation | Module audit status, evidence upload, workflow |
| Lecturer | Evidence preparation and submission | Upload evidence, view checklist status |
| QA Officer | Audit execution and compliance verification | Full audit workflow, findings, approvals |
| System Administrator | Platform configuration | User management, institution settings |
| Student | Beneficiary of quality education | Read-only view of programme quality status |

### 5.2 External Stakeholders

| Stakeholder | Relationship to AQAA |
|-------------|---------------------|
| CHE (Council on Higher Education) | Sets accreditation standards that AQAA enforces |
| DHET (Dept of Higher Education and Training) | Regulates institutions; AQAA tracks DHET compliance |
| SAQA (South African Qualifications Authority) | NQF registration; AQAA stores NQF levels per programme |
| ECSA | Engineering programme accreditation; AQAA supports evidence collection |
| SACAI / UMALUSI | TVET/school accreditation (future scope) |

---

## 6. User Personas

### Persona 1 — Grace: QA Officer

**Profile:** 8 years experience in academic quality assurance at a university of technology. Responsible for coordinating audits across 4 faculties, 200+ modules. Currently uses spreadsheets and email to track evidence. Attends CHE site visits annually.

**Goals:**
- Complete all module folder audits before accreditation cycle
- Track which modules are missing critical evidence
- Generate summary compliance reports for the Deputy VC

**Pain Points:**
- Cannot audit all modules — too many, too little time
- Evidence exists but is not organised — lecturers email PDFs ad hoc
- Cannot demonstrate compliance improvement over time
- CHE visit preparation takes weeks of manual checking

**How AQAA Helps:**
- AI agents pre-check evidence gaps before manual review
- Centralised evidence upload with structured categorisation
- One-click compliance report per faculty, department, or module
- Audit history shows year-on-year improvement

---

### Persona 2 — Dr. Brian: Programme Coordinator

**Profile:** 5 years as Programme Coordinator for BSc Computer Science, 15 modules per year. Collects evidence from 5 lecturers. Submits module folders quarterly. Technically comfortable but not a QA specialist.

**Goals:**
- Know exactly what documents are needed for each module
- Track which lecturers have uploaded their evidence
- Submit complete folders to QA Officer on time

**Pain Points:**
- Unclear on what "complete evidence" means for each module
- Constantly chasing lecturers for missing documents
- Cannot see overall compliance status at a glance

**How AQAA Helps:**
- Clear 10-item checklist per module with current status
- Evidence upload linked directly to checklist items
- Dashboard showing which modules are at-risk or non-compliant
- Workflow notifications when lecturers upload or miss evidence

---

### Persona 3 — Dr. Alice: Lecturer

**Profile:** Teaches Introduction to Programming (100 students). Responsible for uploading course outline, assessment briefs, marked samples, attendance registers. Not deeply familiar with QA requirements. Limited time.

**Goals:**
- Know exactly what to upload and where
- Upload evidence quickly without navigating complex systems
- Not get flagged as non-compliant

**Pain Points:**
- QA requirements feel bureaucratic and unclear
- Uploading documents is manual and fragmented
- No feedback on whether submissions are complete

**How AQAA Helps:**
- Simple upload interface with clear evidence categories
- Instant checklist update when evidence is uploaded
- Visual compliance indicator shows what's still needed

---

### Persona 4 — Prof. Nomsa: Faculty Dean

**Profile:** Dean of the Faculty of ICT, 4 departments, 40 modules. Responsible for faculty-level quality in accreditation submissions. Attends CHE panels.

**Goals:**
- Faculty-level compliance overview at a glance
- Identify high-risk departments before CHE visits
- Generate evidence of continuous quality improvement

**Pain Points:**
- No visibility into individual module compliance without manual checking
- Cannot detect systemic issues across departments
- CHE visit reports take weeks to compile

**How AQAA Helps:**
- Faculty dashboard with department-level compliance breakdown
- Risk alerts for modules below 70% compliance
- Trend view across academic years

---

## 7. Functional Requirements

### 7.1 Authentication and Access Control

| FR-AUTH-001 | Multi-role login with JWT | Must |
| FR-AUTH-002 | 7-level RBAC hierarchy | Must |
| FR-AUTH-003 | httpOnly cookie token storage | Must |
| FR-AUTH-004 | Session refresh (60-min access, 7-day refresh) | Must |
| FR-AUTH-005 | Account deactivation (not deletion) | Must |
| FR-AUTH-006 | Role-based page visibility | Must |

### 7.2 Institution Hierarchy Management

| FR-HIER-001 | Full CRUD: Institution → Faculty → Department → Programme → Module | Must |
| FR-HIER-002 | Multi-campus support per institution | Must |
| FR-HIER-003 | Programme NQF level, credits, status | Must |
| FR-HIER-004 | Module-lecturer assignment | Must |
| FR-HIER-005 | Academic year tracking per module | Must |

### 7.3 Manual QA Audit Engine

| FR-AUDIT-001 | Create module folder audit with 10-item checklist | Must |
| FR-AUDIT-002 | Checklist status: Compliant / Partial / Missing / N/A | Must |
| FR-AUDIT-003 | Compliance % calculation: (compliant + partial×0.5) / (total−N/A) | Must |
| FR-AUDIT-004 | Auto-status: COMPLIANT ≥90%, AT_RISK 70–89%, NON_COMPLIANT <70% | Must |
| FR-AUDIT-005 | Auditor notes per audit | Must |
| FR-AUDIT-006 | Audit list, filter, search | Must |

### 7.4 Evidence Management

| FR-EV-001 | File upload (multipart, up to 50 MB) | Must |
| FR-EV-002 | Evidence linked to specific checklist item and audit | Must |
| FR-EV-003 | Evidence categories aligned to document types | Must |
| FR-EV-004 | Inline preview: PDF, image, text | Must |
| FR-EV-005 | Download evidence | Must |
| FR-EV-006 | Delete evidence (QA Officer+) | Must |
| FR-EV-007 | Evidence upload notification to checklist | Must |

### 7.5 AI Audit Agents

| FR-AI-001 | Module Folder Audit agent | Must |
| FR-AI-002 | Assessment Compliance agent | Must |
| FR-AI-003 | Moderation Compliance agent | Must |
| FR-AI-004 | Attendance Compliance agent | Must |
| FR-AI-005 | Evidence Verification agent | Must |
| FR-AI-006 | Outcome Alignment agent | Must |
| FR-AI-007 | Accreditation Readiness agent | Must |
| FR-AI-008 | Programme Review agent | Must |
| FR-AI-009 | Async trigger → poll pattern (HTTP 202 + run_id) | Must |
| FR-AI-010 | Findings with severity (Critical/High/Medium/Low/Info) | Must |

### 7.6 Audit History and Timeline

| FR-HIST-001 | Immutable event log per audit | Must |
| FR-HIST-002 | Events: created, checklist updated, evidence uploaded/deleted, status changed, compliance changed, notes updated, comment added, workflow changed | Must |
| FR-HIST-003 | Timeline display in Audit Detail page | Must |
| FR-HIST-004 | Actor attribution for every event | Must |

### 7.7 Workflow Engine

| FR-WF-001 | 9-state workflow: Draft → Assigned → Evidence Collection → Pending QA Review → Returned for Corrections → Approved → Rejected → Completed → Archived | Must |
| FR-WF-002 | Audit assignment (assigned_to, assigned_by, due_date, priority, remarks) | Must |
| FR-WF-003 | Role-restricted workflow transitions | Must |
| FR-WF-004 | Approval actions: approve, reject, return, request-evidence | Must |
| FR-WF-005 | Workflow history visible in audit timeline | Must |

### 7.8 Comments and Collaboration

| FR-COM-001 | Comment thread per audit | Must |
| FR-COM-002 | Comment edit (author or SA only) | Must |
| FR-COM-003 | Comment resolve (QA Officer+) | Must |
| FR-COM-004 | Comment delete (author or SA only) | Must |
| FR-COM-005 | Institution-scoped comment access | Must |

### 7.9 Notifications

| FR-NOT-001 | 10 notification types (assigned, due soon, overdue, evidence uploaded/missing, returned, approved, rejected, completed, new comment) | Must |
| FR-NOT-002 | Mark single notification as read | Must |
| FR-NOT-003 | Mark all notifications as read | Must |
| FR-NOT-004 | Filter: all / unread | Must |
| FR-NOT-005 | Email notification templates (delivery service deferred) | Should |

### 7.10 Dashboard and Analytics

| FR-DASH-001 | Entity counts: institutions, faculties, departments, programmes, modules, users | Must |
| FR-DASH-002 | Workflow status summary (4 active states) | Must |
| FR-DASH-003 | Role-scoped dashboard (SA sees platform-wide; others see own institution) | Must |

### 7.11 Institutional Knowledge Package

| FR-IKP-001 | Versioned JSON knowledge packages per institution | Must |
| FR-IKP-002 | Provenance envelope on every knowledge object | Must |
| FR-IKP-003 | Confidence scoring (0.0–1.0) per field | Must |
| FR-IKP-004 | Block low-confidence data (<0.70) from loading | Must |
| FR-IKP-005 | 9-stage ingestion pipeline | Must |
| FR-IKP-006 | Human review queue for medium-confidence fields | Should |
| FR-IKP-007 | IKP management UI | Should (Phase 6) |

### 7.12 Audit Calendar

| FR-CAL-001 | Month-grid calendar showing audit due dates | Must |
| FR-CAL-002 | Colour-coded by workflow status | Must |
| FR-CAL-003 | "No due date" sidebar list | Must |
| FR-CAL-004 | Navigate to audit from calendar event | Must |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Requirement | Target |
|------------|--------|
| API response time (p50) | < 200ms |
| API response time (p95) | < 500ms |
| AI agent completion (p95) | < 30 seconds per module |
| File upload throughput | ≥ 10 MB/s |
| Dashboard load time | < 1 second |
| Concurrent users (pilot) | ≥ 50 |
| Concurrent users (production) | ≥ 500 |

### 8.2 Reliability

| Requirement | Target |
|------------|--------|
| Availability SLA (development) | 99% |
| Availability SLA (production) | 99.5% |
| Backup frequency | Daily |
| Recovery Point Objective (RPO) | 24 hours |
| Recovery Time Objective (RTO) | 4 hours |

### 8.3 Security

| Requirement | Target |
|------------|--------|
| Authentication | JWT HS256, httpOnly cookies |
| Password hashing | bcrypt |
| Transport security | HTTPS only in production |
| Token expiry | Access: 60 min; Refresh: 7 days |
| SQL injection | Parameterised queries (SQLAlchemy) |
| XSS | No token in JS-accessible storage |
| CSRF | SameSite cookie + CORS policy |
| Data isolation | Row-level tenant isolation |

### 8.4 Scalability

| Requirement | Target |
|------------|--------|
| Institutions per deployment | ≥ 50 |
| Modules per institution | ≥ 500 |
| Evidence files per module | ≥ 50 |
| Audit runs per day | ≥ 1,000 |
| Horizontal scaling | Stateless backend, connection pooling |

### 8.5 Maintainability

| Requirement | Target |
|------------|--------|
| Backend test coverage | 432+ tests, 100% pass rate maintained |
| TypeScript errors | 0 at all times |
| Documentation coverage | All subsystems documented |
| Migration strategy | Alembic, always forward-compatible |

### 8.6 Accessibility

| Requirement | Target |
|------------|--------|
| Language | English (South African) |
| WCAG compliance | Level A minimum (Level AA target) |
| Screen reader | Semantic HTML, ARIA labels |
| Keyboard navigation | All core workflows keyboard-navigable |

---

## 9. AI Capabilities

### 9.1 Current AI Agent Portfolio

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| Module Folder Audit | Verifies presence of all required document types | Module files | Findings per document type |
| Assessment Compliance | Checks assessment documentation completeness | Assessment files | Compliance score + findings |
| Moderation Compliance | Verifies internal and external moderation records | Moderation files | Compliance findings |
| Attendance Compliance | Checks attendance evidence coverage | Attendance records | Risk level + gaps |
| Evidence Verification | Cross-validates evidence against learning outcomes | All module files | Verification status |
| Outcome Alignment | Maps assessments to stated learning outcomes | Outcomes + assessments | Alignment score |
| Accreditation Readiness | Assesses module readiness for accreditation | All evidence | Readiness score |
| Programme Review | Reviews full programme across all modules | All programme data | Programme report |

### 9.2 AI Architecture Constraints

- All AI agents are asynchronous (HTTP 202 pattern)
- AI findings are recommendations — humans make final compliance decisions
- All agent files in `backend/app/agents/` are protected (no modification without authorisation)
- Confidence scores attached to all findings

### 9.3 Future AI Capabilities (Planned)

| Capability | Phase |
|-----------|-------|
| IKP-aware audit templates | Phase 7 |
| Natural language QA queries | Phase 7 |
| Predictive gap detection | Phase 7 |
| Cross-institution benchmarking | Phase 8 |
| Automated evidence classification | Phase 7 |

---

## 10. Institutional Knowledge Package

### 10.1 Summary

The IKP is a version-controlled, provenance-tagged knowledge container for each institution. It is the single source of truth for all institutional academic data in AQAA.

Key properties:
- 8-layer structure (Institution → AI Knowledge → Metadata)
- Immutable sealed versions
- Per-field confidence scoring (0.0–1.0)
- 9-stage data ingestion pipeline
- Multi-institution support without code changes

### 10.2 IKP Layers

| Layer | Contents |
|-------|---------|
| 1 — Institution | Profile, codes, campuses, contacts, accreditation |
| 2 — Academic Structure | Faculties, departments, programmes, modules |
| 3 — Curriculum | Learning outcomes, assessments, credit structure |
| 4 — Quality Assurance | QA policies, audit templates, compliance thresholds |
| 5 — Qualification | NQF, credits, APS, admission requirements |
| 6 — Institutional Policy | Academic regulations, exam rules, WIL, RPL |
| 7 — AI Knowledge | Reasoning rules, risk models, prompt templates |
| 8 — Metadata | Provenance, versioning, confidence, review status |

### 10.3 Current IKP Status

| Institution | Status | Scope |
|-------------|--------|-------|
| GFU (demo) | No IKP — seed data | Full hierarchy |
| RCT (demo) | No IKP — seed data | Full hierarchy |
| TUT (pilot) | v1.0.0-draft — HTML only | ICT Faculty |

---

## 11. Qualification Intelligence

### 11.1 Vision

AQAA shall become the definitive platform for qualification-level intelligence in South African higher education — enabling AI-driven analysis of how a module's evidence stack aligns with the requirements of its NQF level, credit weight, and accreditation standards.

### 11.2 NQF-Aware Compliance

| NQF Level | Expected Evidence Complexity | AQAA Behaviour |
|-----------|----------------------------|---------------|
| 5 (HC) | Basic compliance evidence | Lower complexity checklist |
| 6 (Diploma) | Full module documentation | Standard checklist (10 items) |
| 7 (Adv Diploma / BEngTech) | Professional competency evidence + WIL | Enhanced checklist + WIL verification |
| 8 (PGDip / Honours) | Research methodology evidence | Research-focused checklist |
| 9 (Masters) | Original research + supervision records | Research audit template |
| 10 (Doctorate) | Thesis + examination records | Doctoral audit template |

### 11.3 APS and Admission Intelligence (Planned)

Future IKP-aware agents will cross-reference:
- Enrolled student APS against programme admission requirements
- Evidence of prior qualification for RPL candidates
- Credit recognition across articulation pathways

---

## 12. Reporting and Analytics

### 12.1 Current Reporting (Available)

| Report | Description | Access Level |
|--------|-------------|-------------|
| Module compliance score | Current % compliance with status | All staff |
| Audit checklist detail | Per-item status + evidence | Coordinator+ |
| Audit timeline | Full event history | Coordinator+ |
| Workflow status summary | Count by workflow state | Coordinator+ |

### 12.2 Planned Reporting (Phase 6–7)

| Report | Description | Beneficiary |
|--------|-------------|-------------|
| Faculty compliance dashboard | All modules in a faculty with risk flags | Dean, QA Officer |
| Department trend report | Compliance % by academic year | HOD |
| CHE evidence pack summary | Evidence presence per accreditation criterion | QA Officer |
| Compliance heat map | Risk by programme × criterion | QA Officer, Dean |
| Year-on-year improvement report | Compliance score change across IKP versions | VC, Dean |
| Evidence gap report | Modules with critical evidence missing | QA Officer |
| Audit completion rate | % of modules audited by due date | QA Officer |

### 12.3 Analytics Architecture (Planned)

- Read replicas for analytics queries (avoid impacting transactional DB)
- Time-series compliance trend storage
- IKP version comparison API (compare 2025 vs 2026 programme data)
- Export to PDF/Excel for regulatory submissions

---

## 13. Security and Governance

### 13.1 Authentication and Authorisation

| Control | Implementation |
|---------|---------------|
| Token signing | HS256 with `SECRET_KEY` from environment variable |
| Cookie security | httpOnly, Secure flag, SameSite=Lax |
| RBAC | 7-level cumulative hierarchy, enforced in FastAPI dependencies |
| Tenant isolation | `institution_id` on all data rows, enforced in service layer |
| Admin override | SYSTEM_ADMIN bypasses tenant filtering only |

### 13.2 Data Governance

| Governance Area | Policy |
|----------------|--------|
| Data retention | 7 years minimum (academic regulatory requirement) |
| Audit trail | All QA actions recorded in `audit_history` (immutable) |
| IKP provenance | Every knowledge record traceable to official source |
| User deactivation | Accounts deactivated, not deleted; replaced with anonymised token |
| POPIA compliance | Personal data minimisation; no unnecessary PII storage |

### 13.3 File Security

| Control | Implementation |
|---------|---------------|
| Max file size | 50 MB |
| MIME type validation | At upload time |
| Virus scan states | `pending → scanning → ready | quarantined | failed` |
| File path | Server-controlled (`evidence/{inst_id}/{audit_id}/{uuid}{ext}`) |
| Access control | Evidence scoped to institution; download requires auth |

---

## 14. Success Metrics

### 14.1 Product Metrics

| Metric | Pilot Target | Production Target |
|--------|-------------|------------------|
| Modules audited digitally | 100% of ICT Faculty modules | 100% of institution |
| Evidence upload completion rate | ≥ 80% per semester | ≥ 90% per semester |
| AI agent adoption | ≥ 50% of audits use at least 1 agent | ≥ 80% |
| Average time to complete audit | < 2 hours (vs. current 2 days) | < 1 hour |
| Audit compliance score accuracy | Validated against manual check | ≥ 95% agreement |

### 14.2 Quality Metrics

| Metric | Target |
|--------|--------|
| Backend test pass rate | 100% always |
| API uptime | ≥ 99.5% |
| Mean time to fix critical bug | < 24 hours |
| IKP data accuracy | ≥ 95% verified fields |

### 14.3 Institutional Metrics

| Metric | Interpretation |
|--------|---------------|
| % modules at COMPLIANT | Institution health indicator |
| % modules AT_RISK or NON_COMPLIANT | Intervention priority |
| Average evidence completeness per category | Identifies systemic gaps |
| Workflow completion rate | Operational efficiency |

---

## 15. Product Roadmap

### Near-Term (2026)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 5.4D | Documentation Standard | ✅ Complete |
| 5.4E | Product Foundation Documents | 🔄 In Progress |
| 5.4F | Document Intelligence Engine Architecture | ⏳ Planned |
| 5.4G | TUT PDF Extraction (pdfminer.six) | ⏳ Planned |
| 5.4H | TUT ICT Pilot Database Load | ⏳ Planned |

### Medium-Term (2026–2027)

| Phase | Deliverable |
|-------|-------------|
| 6 | IKP Management UI + Full TUT Data |
| 6.1 | Second institution pilot (UP or DUT) |
| 7 | AI Knowledge Base Integration |
| 7.1 | IKP-aware AI agents |

### Long-Term (2027+)

| Phase | Deliverable |
|-------|-------------|
| 8 | Multi-institution production deployment |
| 9 | TVET college support |
| 10 | International institution support |

---

## 16. Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Institutional resistance to digital QA | Medium | High | Pilot with champions; demonstrate time savings |
| PDF extraction quality from TUT prospectus | High | High | Use pdfminer.six; validate extracted data against secondary sources |
| Data provenance errors in IKP | Medium | Critical | Confidence scoring blocks uncertain data; human review gate |
| AI agent false positives (incorrect findings) | Medium | High | Human review required for all AI findings before approval |
| CHE not accepting AI-generated reports | Low | Critical | Reports clearly marked "AI-assisted; human-verified"; humans sign off |
| Session/context loss across development sessions | High | Medium | Documentation standard (Phase 5.4D) mitigates this |
| Multi-tenant data leak | Low | Critical | Triple-layer isolation; automated tenant isolation tests |
| Dependency version conflicts | Medium | Medium | Pin all versions; test on upgrade |

---

## 17. Constraints

### 17.1 Technical Constraints

| Constraint | Source | Impact |
|-----------|--------|--------|
| `@base-ui/react` — no `asChild` prop | ShadCN install choice | Cannot use standard Radix patterns |
| `python -m` prefix on Windows | Windows PATH | All CLI tools invoked via module |
| `pdftoppm` unavailable | Windows environment | Must use `pdfminer.six` for PDF extraction |
| httpOnly cookies only | Security architecture | No client-side token access |
| No direct FastAPI calls from browser | Auth proxy pattern | All calls via `/api/proxy/` |

### 17.2 Regulatory Constraints

| Constraint | Source |
|-----------|--------|
| CHE minimum evidence standards | Council on Higher Education |
| NQF credit minimum per qualification type | HEQSF (SAQA) |
| POPIA data protection | South African law |
| DHET PQM registration | Required for AQAA to reference valid programmes |
| 7-year data retention | Regulatory requirement for academic records |

### 17.3 Scope Constraints

| Out of Scope | Reason |
|-------------|--------|
| Student Information System (SIS) | Different domain; separate regulatory environment |
| Learning Management System (LMS) | Different domain; separate deployment |
| Financial management | Different domain; different compliance framework |
| SMTP email delivery | Infrastructure dependency not yet configured |

---

## 18. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|---------|
| Real-time collaboration | Multiple users editing the same audit checklist | Medium |
| External moderation workflow | Invite external examiners to review findings | High |
| Student portal | Students see programme compliance status (read-only) | Low |
| Mobile application | Field evidence capture via mobile device | Medium |
| API webhooks | Notify external systems (SIS, LMS) of compliance events | Low |
| CHE direct submission | Export audit reports in CHE-specified format | High |
| SAQA NQF API integration | Verify NQF levels in real time from SAQA | Medium |
| Bulk audit triggers | Trigger AI agent for all modules in a department simultaneously | High |
| Academic year rollover | Auto-create next year's audits from previous year | High |
| Comparative benchmarking | Anonymous cross-institution compliance comparison | Medium |

---

*This PRD is a living document. Update it when product strategy, scope, or requirements change.*  
*Reference: `docs/12_Decisions/ADR-*.md` for architectural decisions that implement these requirements.*
