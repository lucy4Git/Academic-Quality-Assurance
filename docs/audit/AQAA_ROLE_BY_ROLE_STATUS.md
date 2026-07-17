# AQAA Role-by-Role Status

**Audit Date:** 2026-07-13  
**Evidence Source:** Live browser testing (4 roles), RBAC code inspection, route permission matrix  
**Seeded Users:** All share password `ChangeMe123!`

---

## System Administrator — `admin@test.com`

**Live Test:** PASSED (2026-07-12)

### What Works
- Full 5-workspace sidebar (Home, Workspace, Knowledge, Quality, Administration) ✅
- Home shows cross-institution stats: 26 institutions, 2327 modules, 748 programmes, 7 open findings ✅
- Quick Actions include admin-specific items: Institutions, Users, AI Providers ✅
- AI prompts: cross-institution analysis variants ✅
- Continue Working: Institution Overview, User Management, AI Workspace ✅
- AI Workspace: streaming responses, institution selector ✅
- `GET /api/v1/institutions` → 28 institutions ✅
- `GET /api/v1/providers/health` → provider status ✅

### Known Gaps
- Settings pages are all Placeholder (cannot change profile, notifications, security, system config)
- Findings page is Placeholder
- Accreditation page is Placeholder
- Calendar page (not inspected)
- Role management, permission management cards link to unimplemented routes

### Access Level
All routes; no restrictions.

---

## Quality Assurance Officer — `qa.officer@tut.ac.za` (TUT)

**Live Test:** PASSED (2026-07-12)

### What Works
- 4-workspace sidebar (Home, Workspace, Knowledge, Quality — no Administration) ✅
- Institution label: "Tshwane University of Technology" ✅
- Health score tile: 87 / Good standing ✅
- Stats: 318 modules, 70 programmes (institution-scoped) ✅
- Quick Actions: Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports ✅
- AI prompts: QA-focused (audit findings, evidence gaps, accreditation, NQF) ✅
- Tenant isolation: cannot see other institutions ✅
- Audit Centre: real implementation (AuditCentre.tsx) ✅
- Knowledge extraction review workspace ✅
- Can trigger audits (COORDINATOR_AND_ABOVE) ✅

### Known Gaps
- Findings page is Placeholder (cannot browse findings list)
- Accreditation page is Placeholder
- Compliance report page is Placeholder
- Settings pages are all Placeholder

### Access Level
Own institution only; all QA features.

---

## Quality Assurance Officer — `qa.officer@up.ac.za` (UP)

**Live Test:** Listed in validation report as PASSED, but UP QA officer was not independently verified in this audit session (TUT session only confirmed live). Trust based on tenant isolation logic being symmetric.

### Expected Behaviour
Identical to TUT QA officer but scoped to University of Pretoria data.

---

## Faculty Dean — `dean.engineering@tut.ac.za` (expected seeded user)

**Live Test:** NOT PERFORMED in this audit.

### Expected Behaviour Based on RBAC
- Sidebar: Home, Workspace, Knowledge, Quality
- Can trigger audits (FACULTY_DEAN ≥ COORDINATOR)
- Cannot access Administration sidebar
- Data scoped to their faculty

### RBAC Position
`faculty_dean` is role 3 in the hierarchy (above HOD, below QA officer).

---

## Head of Department

**Live Test:** NOT PERFORMED.

### Expected Behaviour Based on RBAC
- Sidebar: Home, Workspace, Knowledge, Quality
- Can trigger audits
- Data scoped to department
- Cannot access Reports (requires QA_AND_ABOVE — based on route permission map)

---

## Programme Coordinator

**Live Test:** NOT PERFORMED.

### Expected Behaviour Based on RBAC
- Sidebar: Home, Workspace, Knowledge, Quality
- Can trigger audits (COORDINATOR_AND_ABOVE threshold)
- Can upload evidence
- Data scoped to programme

### Note
The `getContinueCards(role)` default branch (coordinator+) returns: Upload Evidence, Audit Centre, AI Workspace. This is the only role where `/audits` is included in Continue Working.

---

## Lecturer — `lecturer.cs@tut.ac.za` (TUT)

**Live Test:** PASSED (post-fix, 2026-07-12)

### What Works
- 3-workspace sidebar (Home, Workspace, Knowledge — no Quality, no Administration) ✅
- Quick Actions: Knowledge Base, Upload Evidence, AI Workspace ✅
- AI prompts: evidence-focused (upload needs, audit findings, compliance, assessment policy) ✅
- Continue Working: Upload Evidence, Knowledge Base, AI Workspace (no forbidden /audits link) ✅
- Workspace landing: role-specific AI prompts ✅
- Cannot access Quality or Administration sections ✅
- Cannot trigger audits (COORDINATOR_AND_ABOVE required → 403) ✅

### Issues Fixed During Audit
1. Quick Actions was only showing Knowledge Base (too sparse) — fixed by adding Upload Evidence + AI Workspace
2. Continue Working included `/audits` (coordinator-only) — fixed with lecturer-specific branch

### Known Gaps
- Upload Evidence page: exists but no files uploaded (not a bug, just empty state)
- Settings all Placeholder
- If lecturer tries `/quality` or `/audits`, redirected to dashboard

### Access Level
Own modules only; evidence upload; knowledge; AI.

---

## Student — `student.cs@tut.ac.za` (TUT)

**Live Test:** PASSED (2026-07-12)

### What Works
- 1-workspace sidebar (Home only) ✅
- No health score or stat tiles ✅
- Quick Actions: AI Workspace, Programmes only ✅
- AI prompts: programme discovery, QA explanation, NQF levels, resources ✅
- Getting Started panel with 3 accessible items ✅
- About AQAA panel explaining the platform ✅
- Continue Working: Browse Programmes, Knowledge Base, Ask AQAA ✅
- Forbidden route enforcement: /audits → redirect, /quality → redirect, /administration → redirect, /knowledge/acquisition → redirect ✅

### Known Gaps
- No personalised content (programme enrolment, module list) — shows generic student content
- Cannot view their own audit findings related to their programme
- `GET /api/v1/programmes` accessible but no student-specific filtering tested

### Access Level
Read-only across accessible routes (programmes, knowledge base, AI workspace).

---

## Summary Table

| Role | Sidebar Items | Can Trigger Audits | Can Upload | Can Access Findings | Settings |
|------|--------------|-------------------|------------|---------------------|---------|
| system_admin | 5 | ✅ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| quality_assurance_officer | 4 | ✅ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| faculty_dean | 4 | ✅ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| head_of_department | 4 | ✅ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| programme_coordinator | 4 | ✅ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| lecturer | 3 | ❌ | ✅ | ❌ (placeholder) | ❌ (placeholder) |
| student | 1 | ❌ | ❌ | ❌ (placeholder) | ❌ (placeholder) |

**Universal gap:** No role can access the Findings page (PlaceholderPage), Settings pages, or Accreditation Readiness page via the frontend. These are backend-complete / frontend-missing features.
