# AQAA Updated Remaining Issues Register

**Date**: 2026-07-13  
**Sprint**: Post Stage B  

---

## Resolved in Stage B

| Issue | Resolution |
|-------|-----------|
| Finding lifecycle had 10 statuses instead of 12 | ✅ Canonical 12-status enum across all layers |
| `evidence_submitted` / `closed_no_action` semantic mismatch | ✅ Renamed via data migration |
| `REOPENED` went to `IN_PROGRESS` instead of `REOPENED` | ✅ Fixed in routes and state machine |
| `setTimeout` accreditation refresh was fragile | ✅ Replaced with run-ID polling |
| No duplicate prevention for gap promotion | ✅ `gap_promotion_service.py` implemented |
| No `promote-gaps` endpoint | ✅ `POST /{run_id}/promote-gaps` implemented |

---

## Known Remaining Issues

### Medium Priority

| Issue | Location | Notes |
|-------|----------|-------|
| Assignment user-picker not in UI | `FindingsCentre.tsx` | `assigned_to_id` settable via API only; no dropdown in panel |
| "Defer" button not surfaced in UI | `FindingsCentre.tsx` | API endpoint exists (`/defer`); no UI button |
| "Request Review" button not in UI | `FindingsCentre.tsx` | API endpoint exists; submission via API only |
| Dean role not tested in browser | B10 | `dean.ict@tut.ac.za` scenario not explicitly run (covered by HOD-level tests) |

### Low Priority

| Issue | Location | Notes |
|-------|----------|-------|
| `backend/app/models/finding.py` empty stub | `backend/app/models/` | Dead file — `AuditFinding` is in `audit_finding.py` |
| `backend/package-lock.json` untracked | repo root | Should be gitignored |
| `files.py` `@router.delete` with `status_code=204` | `backend/app/routes/files.py` | Fails host `python -c "from app.main import create_app"` but Docker container uses older FastAPI version where it works |
| 3 pre-existing test failures | `tests/test_ai_assistant.py` | `is_placeholder_mode` attribute checks; pre-date Stage B |

### Out of Scope (Architecture Decisions)

| Item | Notes |
|------|-------|
| MongoDB not wired | Architected but not connected; no sprint has included it |
| Real-time push notifications | Findings UI uses manual refresh; no WebSocket layer |
| Qdrant re-indexing (Stage A) | Completed in Stage A; no regression observed |

---

## Next Recommended Sprint

**Stage C: Assignment UX + Defer/Review UI**

Deliverables:
1. User picker in finding panel for ASSIGN action (HOD role)
2. "Defer" button surfaced in Coordinator/HOD panel
3. "Request Review" button surfaced for Lecturers (IN_PROGRESS state)
4. Dean role browser scenario
5. Delete empty `backend/app/models/finding.py`
6. Fix `files.py` `status_code=204` for host Python compatibility
