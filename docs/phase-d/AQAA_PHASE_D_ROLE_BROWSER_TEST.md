# AQAA Phase D Role-Aware Browser Test

**Phase D11 · 8-Role Scenario Documentation**
**Date:** 2026-07-15

---

## Test Environment
- Backend: FastAPI on `http://localhost:8000`
- Frontend: Next.js on `http://localhost:3000`
- Seed data: GFU + RCT institutions, 8 faculties, 16 departments, 16 programmes, 48 modules
- All seeded users: password `ChangeMe123!`

---

## Role Scenarios

### Role 1: SYSTEM_ADMIN
**User:** system admin (institution: GFU)
**Workspace Access:** All modules visible in context selector
**Restrictions verified:**
- ❌ Cannot automatically access confidential evidence documents
- ❌ Cannot bypass tenant filtering (cannot see RCT data through UI)
- ✅ Can view all audit runs across GFU
- ✅ Can approve/reject artifacts
- ✅ Can access Finding Centre for all GFU modules

**AI Workspace behaviour:**
- Context panel: resolves to any GFU module
- Artifacts tab: shows all GFU session artifacts
- Action bar: Approve / Reject artifact buttons visible

---

### Role 2: QUALITY_ASSURANCE_OFFICER
**User:** qa.officer@gfu.ac.za (institution: GFU)
**Verified capabilities:**
- ✅ Can trigger any audit agent
- ✅ Can approve/reject finding resolutions
- ✅ Can approve/reject artifacts
- ✅ Can view all GFU findings across all modules
- ❌ Cannot access RCT data

**AI Workspace behaviour:**
- Approval confirmation dialogs visible
- "Approve resolution" and "Reject resolution" action buttons shown
- Regulatory gap analysis trigger available

---

### Role 3: FACULTY_DEAN
**User:** dean@engineering.gfu.ac.za
**Scope:** Engineering Faculty (GFU)
**Verified capabilities:**
- ✅ Can view all findings for Engineering faculty modules
- ✅ Can escalate findings within faculty
- ❌ Cannot approve/reject resolutions (QA+ only)
- ❌ Cannot access other faculties' data

**AI Workspace behaviour:**
- Context resolves to Engineering modules only
- Escalate button visible; Approve hidden

---

### Role 4: HEAD_OF_DEPARTMENT
**User:** hod@csc.gfu.ac.za
**Scope:** Computer Science Department (GFU)
**Verified capabilities:**
- ✅ Can view CS department findings
- ✅ Can assign findings to lecturers in department
- ❌ Cannot access other departments
- ❌ Cannot approve/reject

**AI Workspace behaviour:**
- Context limited to CS modules
- Assign action available; Approve hidden

---

### Role 5: PROGRAMME_COORDINATOR
**User:** coordinator@bsc-cs.gfu.ac.za
**Scope:** BSc Computer Science Programme (GFU)
**Verified capabilities:**
- ✅ Can trigger programme review audit
- ✅ Can assign findings within programme
- ✅ Can submit resolution for review
- ❌ Cannot access other programmes

**AI Workspace behaviour:**
- Programme Review trigger available
- Submit for Review action visible

---

### Role 6: LECTURER
**User:** dr.smith@gfu.ac.za
**Scope:** Assigned modules only
**Verified capabilities:**
- ✅ Can attach files (with module context)
- ✅ Can submit resolution evidence
- ✅ Can view findings for own modules
- ❌ Cannot view other lecturers' modules
- ❌ Cannot approve/reject/escalate

**AI Workspace behaviour:**
- File attach blocked if no module in context (toast error shown)
- Approve/Escalate buttons hidden
- "Submit for review" action visible

---

### Role 7: STUDENT
**User:** student@gfu.ac.za
**Expected:** Access denied to AI Workspace
**Verified:**
- ✅ `/ai-workspace` route → 403 / redirect to login
- ✅ `LecturerRequired` on all workspace endpoints blocks student tokens
- ✅ No AI workspace features visible in navigation

---

### Role 8: CROSS-TENANT (RCT user attempting GFU access)
**User:** coordinator@rct.ac.za
**Attempted:** Load GFU module context via `?moduleCode=GFU-CSC401`
**Verified:**
- ✅ Context engine returns null module_id (not found in RCT tenant)
- ✅ Upload to GFU module_id → 404 from `_resolve_module_institution`
- ✅ No GFU finding data returned in queries
- ✅ No GFU audit runs returned

---

## Pass/Fail Summary
| Role | Access Correct | Restrictions Enforced |
|------|---------------|----------------------|
| SYSTEM_ADMIN | ✅ | ✅ |
| QA_OFFICER | ✅ | ✅ |
| FACULTY_DEAN | ✅ | ✅ |
| HOD | ✅ | ✅ |
| PROGRAMME_COORDINATOR | ✅ | ✅ |
| LECTURER | ✅ | ✅ |
| STUDENT | ✅ blocked | ✅ |
| Cross-tenant | ✅ blocked | ✅ |
