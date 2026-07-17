# AQAA Stage B — Browser Evidence Log

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B10)  

---

## Evidence Summary

All browser interactions were performed via the Claude Browser MCP against `http://localhost:3000` (live dev server).

---

## Session 1: TUT QA Officer

**User**: `qa.officer@tut.ac.za`  
**Role**: QUALITY_ASSURANCE_OFFICER

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| View findings | `/findings` | 15 total, 15 open, 5 critical |
| Open finding panel | `/findings` | Description, recommendation, audit trail rendered |
| Click Acknowledge | `/findings` | Status → Acknowledged; open count 15→14 |
| Click Escalate | `/findings` | Status → Escalated; rose badge |
| Audit trail | Panel | `[open → acknowledged]` and `[open → escalated]` entries |

---

## Session 2: Programme Coordinator

**User**: `coordinator.it@tut.ac.za`  
**Role**: PROGRAMME_COORDINATOR

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| View findings | `/findings` | 15 total, 11 open (QA Officer's transitions persisted) |
| Open finding (OPEN) | `/findings` | ACTIONS: Acknowledge, Escalate |
| Acknowledge | `/findings` | `Missing: Marking Memo` → Acknowledged; open 11→10 |
| Re-open panel (now ACKNOWLEDGED) | `/findings` | ACTIONS: Start Progress, Escalate |

---

## Session 3: Head of Department

**User**: `hod.cs@tut.ac.za`  
**Role**: HEAD_OF_DEPARTMENT

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| View findings | `/findings` | 15 total, 11 open |
| Open finding (OPEN) | `/findings` | ACTIONS: Acknowledge, Escalate |

---

## Session 4: Lecturer

**User**: `lecturer.cs@tut.ac.za`  
**Role**: LECTURER

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| View findings | `/findings` | 15 findings visible (read access) |
| Open finding panel | `/findings` | Panel opens; ✕ close only |
| ACTIONS section | Panel | **Absent** — no action buttons |
| Sidebar | `/findings` | No "Quality" management link |

---

## Session 5: Student

**User**: `student.cs@tut.ac.za`  
**Role**: STUDENT

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| Navigate to findings | `/findings` | "Access Denied — Your role (student) does not have permission" |

---

## Session 6: Cross-Tenant (UP QA Officer)

**User**: `qa.officer@up.ac.za`  
**Role**: QUALITY_ASSURANCE_OFFICER (UP institution)

| Action | URL | Observed |
|--------|-----|----------|
| Login | `/login` | Redirected to `/` |
| View findings | `/findings` | **0 findings** — cross-tenant isolation confirmed |
| Direct API (TUT finding UUID) | `GET /api/v1/findings/{uuid}` | **403 Forbidden** |

---

## Session 7: Accreditation Workspace (TUT QA Officer)

**User**: `qa.officer@tut.ac.za`

| Action | URL | Observed |
|--------|-----|----------|
| Navigate | `/accreditation` | All TUT modules listed with "Run" buttons |
| Click Run (ACX118G) | `/accreditation` | Immediately shows "Queued… — waiting to start…" |
| Wait 4s | — | Auto-polling updates UI |
| Wait 8s total | — | Score displayed + "View report" link |
| Run button state | — | Disabled during polling (duplicate prevention) |
