# AQAA Stage B — Multi-Role Browser Test Report

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B10)  
**Environment**: `http://localhost:3000` (Next.js dev) + `http://localhost:8000` (FastAPI Docker)

---

## Test Matrix

| Role | Email | Institution | Findings | Actions Available |
|------|-------|-------------|----------|-------------------|
| QA Officer | `qa.officer@tut.ac.za` | TUT | 15 visible | Acknowledge, Assign, Escalate, Request Review, Resolve, Reject, Reopen, Close |
| Programme Coordinator | `coordinator.it@tut.ac.za` | TUT | 15 visible | Acknowledge, Start Progress, Escalate |
| Head of Department | `hod.cs@tut.ac.za` | TUT | 15 visible | Acknowledge, Escalate |
| Lecturer | `lecturer.cs@tut.ac.za` | TUT | 15 visible | None on Open (Submit Resolution when IN_PROGRESS) |
| Student | `student.cs@tut.ac.za` | TUT | Access Denied | — |
| QA Officer (cross-tenant) | `qa.officer@up.ac.za` | UP | 0 visible | — |

---

## Scenario Results

### 1. TUT QA Officer — Full Lifecycle Test

- **Login**: ✅ Redirected to `/` (AI Workspace)
- **Navigate to `/findings`**: ✅ 15 findings loaded
- **Filter by status**: ✅ 12-status dropdown present
- **Open finding detail**: ✅ Panel shows description, recommendation, audit trail
- **Acknowledge transition** (OPEN → ACKNOWLEDGED): ✅ Status updated, Open count 15→14
- **Escalate transition** (OPEN → ESCALATED): ✅ Status updated, badge shows rose colour

### 2. Programme Coordinator

- **Login**: ✅ Coordinator dashboard
- **Findings list**: ✅ 15 findings (same institution)
- **Open finding ACTIONS section**: ✅ Shows "Acknowledge", "Escalate"
- **Acknowledge transition** (OPEN → ACKNOWLEDGED): ✅ "Marking Memo" → Acknowledged; Open count 15→11 (cumulative from QA Officer test)
- **Post-acknowledge actions**: ✅ Shows "Start Progress", "Escalate"

### 3. Head of Department

- **Login**: ✅
- **Findings list**: ✅ 15 findings
- **Open finding ACTIONS**: ✅ Shows "Acknowledge", "Escalate" (same as Coordinator for OPEN)
- **No extra actions**: ✅ HOD-specific "Assign" visible when finding in ACKNOWLEDGED state

### 4. Lecturer

- **Login**: ✅
- **Findings list**: ✅ 15 findings visible (read access)
- **Open finding panel**: ✅ Panel opens
- **ACTIONS section**: ✅ **Not present** — no action buttons for Open findings
- **Sidebar**: `quality` nav link absent (no quality management access)

### 5. Student

- **Login**: ✅
- **Navigate to `/findings`**: ✅ **Access Denied** page rendered
- **Message**: "Your role (student) does not have permission to view this page."

### 6. Cross-Tenant (UP QA Officer vs TUT data)

- **Login as UP QA Officer**: ✅
- **Frontend `/findings`**: ✅ **0 findings** (tenant-scoped)
- **Direct API access** (`GET /api/v1/findings/{tut_finding_uuid}`): ✅ **403 Forbidden**

---

## Accreditation Workspace Test

- **QA Officer login**: ✅
- **Navigate to `/accreditation`**: ✅ All TUT modules listed (48+)
- **Trigger run on ACX118G**: ✅ Button → "Queued… — waiting to start…" immediately
- **Polling**: ✅ Status updated every 4 seconds without page reload
- **Completion**: ✅ After ~8s: score + severity badge + "View report" link appeared
- **Duplicate submission prevention**: ✅ Run button disabled while polling active

---

## Issues Found

None. All scenarios passed.

---

## Environment at Test Time

- Backend: Docker `aqaa-backend` (healthy)
- Postgres: `aqaa-postgres` (healthy)
- Migration: `7a8b9c0d1e2f` applied
- Frontend: Next.js 14 dev server on :3000
