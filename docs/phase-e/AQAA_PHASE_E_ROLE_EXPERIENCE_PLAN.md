# AQAA Phase E — Role Experience Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

> This document defines the intended experience for each of the 8 AQAA roles in Phase E. Each section covers: role goals, primary dashboard, key actions, and AI Workspace behaviour.

---

## 1. System Administrator

### Goals
- Provision and manage institutions and tenants
- Monitor platform health and security
- Manage AI governance and regulatory knowledge

### Primary Dashboard
- Platform overview: active institutions, total users, system health indicators
- AI governance summary: grounding coverage, hallucination incident count
- Security events: cross-tenant attempts, failed MFA, suspicious login patterns
- Background job status: queue depth, last completed jobs

### Key Actions
| Action | Route | Phase E Status |
|--------|-------|---------------|
| Provision new institution | `/admin/institutions/new` | New (tenant provisioning wizard) |
| Ingest regulatory document | `/admin/regulatory-docs` | New |
| Review AI audit logs | `/admin/ai-governance` | New |
| Review hallucination incidents | `/admin/ai-governance/incidents` | New |
| Manage users (all institutions) | `/admin/users` | Existing |
| View DSAR export | `/admin/users/{id}/export` | New |
| View background job log | `/admin/jobs` | New |
| Configure audit trigger schedules | `/admin/schedules` | New |

### AI Workspace Behaviour
- Access to all institution contexts (institution selector in context panel)
- Governance mode: can ask "How many hallucination incidents occurred this week?"
- Platform administration prompts enabled
- No finding actions — admin does not participate in QA finding lifecycle

---

## 2. Quality Assurance Officer

### Goals
- Monitor compliance across all faculties, departments, and programmes
- Manage the full finding and corrective action lifecycle
- Generate and present audit reports to institutional leadership
- Use AI to identify systemic compliance risks

### Primary Dashboard
- Institution compliance score trend (12-month rolling)
- Finding severity breakdown: CRITICAL / HIGH / MEDIUM / LOW open counts
- Faculty compliance heat map (drill-down to department)
- Recent CRITICAL and HIGH findings requiring attention
- Upcoming corrective action due dates
- Audit cycle status: modules audited vs modules pending this period

### Key Actions
| Action | Phase E Status |
|--------|---------------|
| Trigger module audit | Existing |
| View and manage all findings | Existing |
| Create and assign corrective actions | New |
| Generate PDF audit report | New (PDF functional) |
| Generate DOCX audit report | New |
| Export XLSX finding data | New |
| Flag AI response as hallucination | New |
| Upload institutional policy document | New |
| View compliance trend chart | New |
| View faculty heat map | New |
| Compare audit cycles | New |

### AI Workspace Behaviour
- Full access to all module and programme contexts in their institution
- Regulatory actions enabled: cite CHE, DHET, SAQA frameworks
- Finding actions enabled: acknowledge, assign, escalate, close
- Corrective action actions enabled: create CAP, assign due date
- Report generation action: draft executive summary as artifact
- Grounding requirement: ≥ 85% of QA officer responses cite OFFICIAL_VERIFIED sources

---

## 3. Faculty Dean

### Goals
- Understand faculty-wide compliance posture
- Identify departments at risk before formal audit cycles
- Receive executive summaries without navigating detailed audit records

### Primary Dashboard
- Faculty compliance score (rolling 90 days)
- Department compliance heat map — colour-coded by compliance score
- Top 5 CRITICAL findings by department (unresolved)
- Recent audit activity timeline
- Corrective action completion rate by department

### Key Actions
| Action | Phase E Status |
|--------|---------------|
| View faculty heat map | New |
| Drill down to department findings | Existing |
| Request QA Officer attention on a finding | Via finding escalation |
| View faculty-level PDF report | New |

### AI Workspace Behaviour
- Read-only finding access (cannot change finding status)
- Context limited to their faculty's departments and programmes
- AI can generate faculty-level compliance summaries
- Report drafting actions enabled
- Regulatory citation enabled (read-only context)

---

## 4. Head of Department

### Goals
- Manage department-level audit compliance
- Assign findings to Programme Coordinators
- Track corrective action progress across programmes

### Primary Dashboard
- Department compliance score (rolling 90 days)
- Unresolved findings by programme: count and severity breakdown
- Corrective actions: overdue count, approaching due date count
- Recent audit activity by programme
- Module audit coverage: % of modules audited in current period

### Key Actions
| Action | Phase E Status |
|--------|---------------|
| View department findings | Existing |
| Assign finding to Programme Coordinator | Existing (via ASSIGNED status) |
| Create corrective action on finding | New |
| Track corrective action progress | New |
| View department audit report | Existing |

### AI Workspace Behaviour
- Context limited to their department's programmes and modules
- Finding assignment actions enabled
- Corrective action creation and tracking enabled
- Can ask: "Which programmes in my department have unresolved CRITICAL findings?"

---

## 5. Programme Coordinator

### Goals
- Ensure all modules in their programme are audit-ready
- Collect and submit evidence for audit findings
- Track module folder compliance across the programme

### Primary Dashboard
- Programme compliance score
- Module audit status: compliant / needs attention / critical / not yet audited
- Unresolved findings by module
- Pending evidence upload requests
- Upcoming corrective action due dates (assigned to them)

### Key Actions
| Action | Phase E Status |
|--------|---------------|
| Trigger module audit | Existing |
| View programme-level findings | Existing |
| Submit evidence of resolution for corrective action | New |
| Upload module evidence files | Existing |
| View programme review audit | Existing |

### AI Workspace Behaviour
- Context limited to their programme's modules
- Finding evidence submission actions enabled
- Can query: "What evidence is missing for my programme's upcoming accreditation?"
- Regulatory citations from CHE and SAQA enabled

---

## 6. Lecturer

### Goals
- Maintain their module folder in compliance
- Upload required assessment and moderation evidence
- Understand what evidence is needed for upcoming audits

### Primary Dashboard
- Module compliance status: last audit score, overall status badge
- Evidence checklist: what has been uploaded vs what is required
- Unresolved findings on their module
- Upcoming audit schedule (if automated audits are scheduled)

### Key Actions
| Action | Phase E Status |
|--------|---------------|
| Upload module evidence files | Existing |
| View their module's audit results | Existing |
| View findings on their module | Existing |
| Respond to corrective action (provide evidence) | New |
| Ask AI about module compliance requirements | Existing |

### AI Workspace Behaviour
- Context limited to modules they are assigned to
- No finding lifecycle actions (cannot change finding status)
- Restricted action set: can only query and generate compliance checklists
- AI prompts guide them toward: "What do I need to upload to make my module folder compliant?"
- Source citations shown but in simplified form

---

## 7. Student

**Note:** The student role is a limited observer role in Phase E. The student-facing QA experience is explicitly out of scope and deferred to Phase F. The student role is retained to allow students to authenticate and access any institution-specific student-facing features that may be added in future.

### Phase E Student Experience
- Login and home page: "Getting Started" panel with institution name
- View: Any publicly shared QA policies their institution has made visible to students
- AI Workspace: read-only, limited to policy queries. No finding access. No upload capability.
- No dashboard, no analytics, no reports

---

## 8. Institutional Admin (Not a Separate Role — Fulfilled by System Admin at Institution Level)

An institution may designate a user as System Admin for their institution only. In Phase E, this is handled by creating a `SYSTEM_ADMIN` user scoped to a single institution (the System Admin sees only their institution, not all institutions). This is achieved via the existing RBAC — no new role is introduced.

---

## 9. Onboarding Tour (All Roles)

**Trigger:** User's first successful login (tracked via `users.first_login_at` — new column).

**Format:** 5-step overlay tour, role-specific content.

### QA Officer Tour Steps
1. "Welcome to AQAA — Your institution's quality intelligence platform"
2. "This is your compliance dashboard — your institution's audit health at a glance"
3. "The AI Workspace is where you'll spend most of your time — ask anything about your institution's QA status"
4. "When the AI surfaces a finding, you can act on it right here — assign, escalate, or close"
5. "Your citations panel shows exactly which regulatory documents the AI is drawing from — always verified sources"

### Lecturer Tour Steps
1. "Welcome to AQAA — your module compliance assistant"
2. "This is your module dashboard — it shows your last audit result and what's needed"
3. "Upload your evidence files here — assessments, moderation records, attendance"
4. "Your AI assistant can tell you exactly what's required for your next audit — just ask"
5. "If you have an open finding on your module, you'll see it here with what to do next"

---

## 10. Accessibility Requirements Per Role

| Requirement | All Roles |
|-------------|----------|
| All interactive elements keyboard-accessible | Yes |
| Colour contrast ≥ 4.5:1 (WCAG 2.1 AA) | Yes |
| Screen reader compatibility | ARIA labels on all interactive elements |
| Focus management on modal dialogs | Yes |
| Heat map: colour scale must have non-colour indicator (text or pattern) for colour-blind users | Yes (heat map) |

---

## Referenced Documents

- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md) — UX requirements
- [AQAA_PHASE_E_VISION_AND_SCOPE.md](AQAA_PHASE_E_VISION_AND_SCOPE.md) — Workstream E7
- [AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md](AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md) — Pilot user roles
