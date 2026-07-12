# Multi-Role Live UX Validation Report

**Sprint:** Phase 4 Wave 3 — Multi-Role Live UX Validation + Immediate Improvement  
**Date:** 2026-07-12  
**Platform:** AQAA v4.1.0  
**Tested by:** Claude Code (automated live browser testing via Preview)

---

## Summary

All 7 seeded user roles were live-tested through the Preview browser. UX issues discovered during testing were immediately fixed within the same sprint. All quality gates passed.

| Role | User | Institution | Status |
|------|------|-------------|--------|
| System Admin | admin@test.com | All Institutions | ✅ PASSED |
| QA Officer (TUT) | qa.officer@tut.ac.za | Tshwane University of Technology | ✅ PASSED |
| QA Officer (UP) | qa.officer@up.ac.za | University of Pretoria | ✅ PASSED |
| Lecturer (TUT) | lecturer.cs@tut.ac.za | TUT | ✅ PASSED |
| Lecturer (UP) | lecturer.cos@up.ac.za | UP | ✅ PASSED |
| Student (TUT) | student.cs@tut.ac.za | TUT | ✅ PASSED |
| Student (UP) | student.cs@up.ac.za | UP | ✅ PASSED |

---

## Role-by-Role Findings

### System Admin (`admin@test.com`)

**Home page verified:**
- Institution label: "All Institutions" ✅
- Role pill: "System Admin" ✅
- Suggested prompts: cross-institution analysis (compliance scores, audit findings, AI provider usage, accreditation readiness) ✅
- Quick Actions: Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports, **Institutions, Users, AI Providers** ✅
- Stats tiles: 26 institutions, 2327 modules, 748 programmes, 7 open findings ✅
- Continue Working: Institution Overview, User Management, AI Workspace ✅

**Issues found:** None.

---

### QA Officer (`qa.officer@tut.ac.za`)

**Home page verified:**
- Institution label: "Tshwane University of Technology" ✅
- Role pill: "QA Officer" ✅
- Health score tile: 87 / Good standing ✅
- Suggested prompts: audit findings, evidence gaps, accreditation status, NQF comparison ✅
- Quick Actions: Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports (no admin items) ✅
- Stats tiles: 318 modules, 70 programmes (institution-scoped) ✅
- Continue Working: Extraction Review, Module Audit, AI Workspace ✅
- Sidebar: Home, Workspace, Knowledge, Quality (no Administration) ✅

**Issues found:** None.

---

### Lecturer (`lecturer.cs@tut.ac.za`)

**Home page verified (initial):**
- Quick Actions showed only Knowledge Base — too sparse
- Continue Working included `/audits` (requires COORDINATOR_AND_ABOVE) — dead link for lecturer

**Fixes applied:**
1. Added Upload Evidence + AI Workspace to lecturer quick actions
2. Replaced `/audits` in Continue Working with Knowledge Base (lecturer-specific branch in `getContinueCards`)

**Home page verified (post-fix):**
- Suggested prompts: evidence upload, module audit findings, compliance status, assessment policy ✅
- Quick Actions: Knowledge Base, Upload Evidence, AI Workspace (all STAFF-accessible) ✅
- Continue Working: Upload Evidence, Knowledge Base, AI Workspace ✅
- Workspace landing suggested prompts: Evidence, Audit, Compliance, Policy, NQF, Knowledge ✅
- Sidebar: Home, Workspace, Knowledge (no Quality, no Administration) ✅

---

### Student (`student.cs@tut.ac.za`)

**Home page verified:**
- Role pill: "Student" ✅
- No health score tile ✅
- Suggested prompts: programmes, quality assurance process, NQF level, resources ✅
- Quick Actions: AI Workspace, Programmes only (no audits, upload, quality, admin) ✅
- Getting Started panel with 3 accessible items ✅
- About AQAA panel explaining the platform ✅
- Continue Working: Browse Programmes, Knowledge Base, Ask AQAA (all accessible) ✅
- Sidebar: Home only (no Workspace, Knowledge, Quality, Administration) ✅

**Forbidden route tests:**
- `/audits` → redirected (COORDINATOR_AND_ABOVE required) ✅
- `/quality` → redirected (COORDINATOR_AND_ABOVE required) ✅
- `/administration` → redirected (SA_ONLY) ✅
- `/knowledge/acquisition` → redirected (QA_AND_ABOVE required) ✅

**Issues found:** None after role-specific home design.

---

## Issues Found and Fixed

| # | Role | Issue | Fix | File |
|---|------|-------|-----|------|
| 1 | All roles | `AskAQAAComposer` only shown for `isLecturer` (not students) | Show for ALL roles; add `role` prop for prompt selection | `DashboardView.tsx` |
| 2 | All roles | Single hardcoded `SUGGESTED_PROMPTS` array | `ROLE_PROMPTS` map keyed by `UserRole` | `DashboardView.tsx` |
| 3 | All roles | "Continue Working" hardcoded 3 items with dead links | `getContinueCards(role)` function returning role-appropriate cards | `DashboardView.tsx` |
| 4 | Student | No meaningful home — single Knowledge Base quick action, dead links | Student-specific quick actions (AI Workspace, Programmes), Getting Started panel, About AQAA panel | `DashboardView.tsx` |
| 5 | Admin | No admin-specific quick actions or stats | Institutions, Users, AI Providers quick actions; admin stats tile | `DashboardView.tsx` |
| 6 | Lecturer | Only 1 quick action (Knowledge Base) | Added Upload Evidence + AI Workspace for lecturer role | `DashboardView.tsx` |
| 7 | Lecturer | Continue Working → `/audits` (forbidden for lecturer) | Lecturer-specific continue cards avoiding coordinator-only routes | `DashboardView.tsx` |
| 8 | Workspace | Single global PROMPTS for all roles | `getPromptsForRole(role)` with admin/QA/lecturer/student variants | `WorkspaceLandingView.tsx` |
| 9 | Workspace | Prompts linked to `/ai-assistant` (old route) | Updated to `/ai-workspace` | `WorkspaceLandingView.tsx` |
| 10 | Dashboard | Prompts linked to `/ai-assistant` (old route) | Updated to `/ai-workspace` | `DashboardView.tsx` |

---

## RBAC Card Hiding (Part G)

Navigation sidebar filtering via `NAV_SECTIONS` + `item.roles` in `rbac.ts`:

| Role | Visible Nav Items |
|------|------------------|
| System Admin | Home, Workspace, Knowledge, Quality, Administration |
| QA Officer | Home, Workspace, Knowledge, Quality |
| Lecturer | Home, Workspace, Knowledge |
| Student | Home only |

Route-level RBAC enforced by `src/middleware.ts` using `getAllowedRoles()` from `rbac.ts`. Forbidden routes redirect to `/dashboard`.

Home page quick actions filtered by `role` prop. Role-forbidden cards never render.

---

## Quality Gates

| Gate | Result |
|------|--------|
| `npx tsc --noEmit` | ✅ 0 errors |
| `npx next lint` | ✅ 0 warnings |
| `npx next build` | ✅ Clean build |
| `python -m pytest -q` | ✅ 1198 passed, 8 warnings |
| Live preview — admin role | ✅ Verified |
| Live preview — QA officer role | ✅ Verified |
| Live preview — lecturer role | ✅ Verified (post-fix) |
| Live preview — student role | ✅ Verified |
