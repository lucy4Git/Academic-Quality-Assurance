# AQAA Final Release Testing Guide

**Version:** 1.0.0-rc1  
**Date:** 2026-07-03

This guide covers end-to-end role-based testing for RC1. Run through all scenarios before signing off on deployment.

---

## Test Accounts

All seeded accounts share password `ChangeMe123!`.

| Role | Email (example) | Institution | Expected access |
|------|-----------------|-------------|-----------------|
| System Admin | admin@aqaa.ac.za | All | Full platform |
| QA Officer (TUT) | qa.officer@tut.ac.za | TUT | TUT data only |
| QA Officer (UP) | qa.officer@up.ac.za | UP | UP data only |
| Lecturer (TUT) | lecturer.cs@tut.ac.za | TUT | TUT modules only |
| Lecturer (UP) | lecturer.cos@up.ac.za | UP | UP modules only |
| Student (TUT) | student.cs@tut.ac.za | TUT | Read-only programmes/modules |
| Student (UP) | student.cs@up.ac.za | UP | Read-only programmes/modules |

---

## Test Scenarios

### A. Authentication

| # | Action | Expected |
|---|--------|----------|
| A1 | Login with correct credentials | JWT cookie set; redirected to dashboard |
| A2 | Login with wrong password | 401 error shown |
| A3 | Access `/dashboard` without login | Redirected to `/login` |
| A4 | Logout | Cookie cleared; redirected to login |
| A5 | Token expiry (wait 60 min or set short TTL) | Auto-redirect to login |

### B. Dashboard

| # | Role | Expected |
|---|------|----------|
| B1 | System Admin | Sees TUT and UP aggregate counts |
| B2 | QA Officer (TUT) | Sees TUT counts only |
| B3 | QA Officer (UP) | Sees UP counts only |
| B4 | Lecturer | Sees role-appropriate summary |
| B5 | Student | Sees limited dashboard |

### C. Institution Hierarchy (tenant isolation)

| # | Action | Expected |
|---|--------|----------|
| C1 | QA Officer (TUT) views institutions | TUT only visible |
| C2 | QA Officer (UP) views faculties | UP faculties only |
| C3 | System Admin views institutions | TUT and UP visible; GFU/RCT marked archived |
| C4 | QA Officer (TUT) tries to access UP module URL | 403 or empty result |
| C5 | Student tries to access `/institutions` | Redirected to `/forbidden` |

### D. Programmes and Modules

| # | Action | Expected |
|---|--------|----------|
| D1 | Lecturer (TUT) views programmes | TUT programmes only |
| D2 | Student (UP) views modules | UP modules, read-only |
| D3 | Coordinator creates module | Success; module appears in list |
| D4 | Lecturer (TUT) tries to view UP module | 403 |

### E. Audit Agents

| # | Action | Expected |
|---|--------|----------|
| E1 | Trigger Module Folder Audit | HTTP 202; run_id returned |
| E2 | Poll `GET /audits/{run_id}` | Status transitions: running → completed |
| E3 | View completed audit report | Findings with severity shown |
| E4 | Trigger all 8 agent types | All return 202 and complete |

### F. Evidence & Files

| # | Action | Expected |
|---|--------|----------|
| F1 | Upload a PDF to a module | State: pending → scanning → ready |
| F2 | View file library | Only own-institution files shown |
| F3 | Download a file | File served correctly |
| F4 | Upload file > 50MB | Rejected with 413 |

### G. Workflow

| # | Action | Expected |
|---|--------|----------|
| G1 | Create audit workflow | Status: draft |
| G2 | Assign to lecturer | Status: assigned; notification sent |
| G3 | Submit for QA review | Status: pending_qa_review |
| G4 | QA Officer approves | Status: approved |
| G5 | QA Officer rejects with comment | Status: returned_for_corrections |

### H. Knowledge & AI

| # | Action | Expected |
|---|--------|----------|
| H1 | Search knowledge base | Returns TUT/UP chunks; no cross-tenant leakage |
| H2 | QA Officer asks AI Assistant (TUT) | Grounded answer citing TUT sources |
| H3 | Admin asks without institution_code | 422 validation error |
| H4 | Check provider status endpoint | Returns provider name, model, status |
| H5 | Switch to LOCAL_DEV | Amber banner shown in UI |

### I. Qualification Intelligence

| # | Action | Expected |
|---|--------|----------|
| I1 | Enter 5 subjects, calculate | GPA, CGPA, NQF advisory shown |
| I2 | All subjects pass (85%+) | GPA ≈ 4.0; no warnings |
| I3 | One subject fails (<50%) | Warning shown; failed subject highlighted red |
| I4 | 360 credits + bachelor type | NQF Level 7 advisory shown |
| I5 | 120 credits + bachelor type | Credit shortfall warning shown |
| I6 | Save record | Appears in Saved Records tab |
| I7 | Export CSV | CSV downloads with disclaimer header |
| I8 | Delete saved record | Removed from list |
| I9 | Disclaimer always visible | Banner and footer text present |

### J. Analytics & Reports

| # | Action | Expected |
|---|--------|----------|
| J1 | HOD views analytics | Charts with own-institution data |
| J2 | Export CSV | Downloads with UTF-8 BOM |
| J3 | Export Excel | XLSX downloads with metadata sheet |
| J4 | Student tries to access `/analytics` | Redirected to `/forbidden` |

---

## Tenant Isolation Verification

Run these cross-tenant checks specifically:

1. Log in as `qa.officer@tut.ac.za`
2. Note a module ID from TUT
3. Log out, log in as `qa.officer@up.ac.za`
4. Attempt `GET /api/v1/modules/{tut_module_id}` via browser devtools or curl
5. **Expected:** 404 or 403 — UP officer must not see TUT module

Repeat in reverse (UP module, TUT officer).

---

## Quality Gate Results (RC1)

| Gate | Command | Result |
|------|---------|--------|
| Backend tests | `python -m pytest -q` | ✅ 884 passed |
| TypeScript | `npx tsc --noEmit` | ✅ 0 errors |
| ESLint | `npm run lint` | ✅ 0 warnings |
| Production build | `npm run build` | ✅ Clean |

---

## Known Acceptable Limitations for RC1

- PDF export returns plain-text with disclaimer (full reportlab PDF is a post-RC1 enhancement)
- AI responses in LOCAL_DEV mode are template-based (configure OPENAI_API_KEY for real responses)
- No rate limiting on auth endpoints (add before high-traffic go-live)
