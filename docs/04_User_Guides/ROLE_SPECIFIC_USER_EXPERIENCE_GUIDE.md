# Role-Specific User Experience Guide

**AQAA v4.1.0 · Phase 4 Wave 3**

This guide describes the tailored experience each role receives across the Home page, Workspace landing, and AI Workspace.

---

## System Administrator

**Access:** All institutions, all features, global AI scope.

### Home Page
- **Stats:** Institutions count, total modules, total programmes, open findings (cross-institution)
- **Health score:** Shown (87 / Good standing)
- **Quick Actions:** Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports, Institutions, Users, AI Providers
- **AI Prompts:** Cross-institution compliance comparison, open findings by institution, AI provider usage, accreditation readiness
- **Continue Working:** Institution Overview, User Management, AI Workspace

### Workspace Landing
- **AI Prompts:** Admin-scoped (cross-institution analysis, provider monitoring)
- **AI Tools:** All 4 tools visible (AI QA Assistant, AI Workspace, Qualification Intelligence, Institution Workspace)

### Sidebar
Home · Workspace · Knowledge · Quality · **Administration**

---

## Quality Assurance Officer

**Access:** Own institution, all QA features, knowledge acquisition, audit centre, findings.

### Home Page
- **Stats:** Institution-scoped modules, programmes, open findings, evidence files
- **Health score:** Shown
- **Quick Actions:** Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports
- **AI Prompts:** Recent audit findings, evidence gaps, accreditation status, NQF comparison
- **Activity Feeds:** Recent AI Activity + Today's Priorities
- **Continue Working:** Extraction Review, Module Audit, AI Workspace

### Workspace Landing
- **AI Prompts:** QA-focused (audit findings synthesis, knowledge gaps, accreditation readiness, compliance summaries, NQF research, governance)

### Sidebar
Home · Workspace · Knowledge · Quality

---

## Faculty Dean / Head of Department / Programme Coordinator

**Access:** Institution features scaled to their scope; can trigger audits.

### Home Page
- **Quick Actions:** Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports (Reports hidden for HOD and below)
- **AI Prompts:** Scoped to faculty/department/programme as appropriate
- **Activity Feeds:** Recent AI Activity + Today's Priorities
- **Continue Working:** Upload Evidence, Audit Centre, AI Workspace

### Sidebar
Home · Workspace · Knowledge · Quality

---

## Lecturer

**Access:** Own modules; can upload evidence, view knowledge, use AI. Cannot trigger audits.

### Home Page
- **Quick Actions:** Knowledge Base, Upload Evidence, AI Workspace
- **AI Prompts:** Evidence upload needs, module audit findings, compliance status, assessment policy
- **No Activity Feeds** (coordinator-level feature)
- **Continue Working:** Upload Evidence, Knowledge Base, AI Workspace (no audit links)

### Workspace Landing
- **AI Prompts:** Evidence-focused (upload needs, audit findings, compliance, policy, NQF, institutional knowledge)

### Sidebar
Home · Workspace · Knowledge

---

## Student

**Access:** Read-only; can view programmes, modules, knowledge base, and AI Workspace.

### Home Page
- **No health score or stats tiles**
- **Quick Actions:** AI Workspace, Programmes
- **AI Prompts:** Programme discovery, quality assurance explanation, NQF levels, policies, resources, accreditation
- **Getting Started panel:** AI Workspace, Knowledge Base, Programmes (all accessible)
- **About AQAA panel:** Platform explainer with AI Workspace link
- **Continue Working:** Browse Programmes, Knowledge Base, Ask AQAA

### Workspace Landing
Not accessible (Workspace nav item hidden for students). Students access AI through `/ai-workspace` directly via Home page links.

### Sidebar
Home only

---

## RBAC Quick Reference

| Feature | Admin | QA Officer | Dean | HOD | Coordinator | Lecturer | Student |
|---------|-------|-----------|------|-----|-------------|----------|---------|
| Home | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workspace nav | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Knowledge nav | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Quality nav | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Administration nav | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| AI Workspace | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trigger Audits | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Upload Evidence | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Knowledge Acquisition | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Users / Institutions | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| AI Providers | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## AI Suggested Prompts by Role

All prompts on both the Home page and Workspace landing are role-specific. Clicking a prompt navigates to `/ai-workspace` with the query pre-filled.

| Role | Sample Prompt |
|------|--------------|
| Admin | "Compare compliance scores across all institutions" |
| QA Officer | "Which modules need evidence before Friday?" |
| Dean | "Generate an accreditation readiness summary for my faculty" |
| HOD | "Which modules in my department have open findings?" |
| Coordinator | "Summarise audit findings for my programme" |
| Lecturer | "What evidence do I need to upload for my modules?" |
| Student | "What programmes does my institution offer?" |

---

## Technical Implementation

- **`DashboardView.tsx`** — `ROLE_PROMPTS` map, `getContinueCards(role)`, role-conditional rendering via `useRole()` hooks
- **`WorkspaceLandingView.tsx`** — `ALL_PROMPTS` map, `getPromptsForRole(role)` via `useRole()`
- **`rbac.ts`** — `NAV_SECTIONS` with `roles[]` per item; `ROUTE_PERMISSIONS` enforced by middleware
- **`middleware.ts`** — Server-side route guard using `getAllowedRoles()` + `access_token` cookie
