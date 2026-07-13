# AQAA Accreditation Readiness — Stage B Implementation Report

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B8 + B9)  

---

## B8: API Verification + Workflow

### Problem
The accreditation workspace used `setTimeout(3000)` to refresh after triggering a run. This caused:
- Silent failure if the audit took more than 3 seconds
- No way to distinguish PENDING vs RUNNING vs COMPLETED
- No recovery UI for failed runs
- Race conditions if user clicked Run twice

### Fix Applied

**`frontend/src/app/(main)/accreditation/AccreditationWorkspace.tsx`**

Replaced `setTimeout` with TanStack Query polling by run ID:

```typescript
const POLL_INTERVAL_MS = 4000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000;
const TERMINAL_STATUSES = new Set(["completed", "failed"]);
```

State per module card:
- `activeRunId`: UUID of the in-flight run (cleared on terminal)
- `pollStartedAt`: timestamp for timeout calculation

Polling query:
```typescript
refetchInterval: (query) => {
  const status = query.state.data?.run_status;
  if (!status || TERMINAL_STATUSES.has(status)) return false;
  return POLL_INTERVAL_MS;
}
```

`useEffect` syncs: when terminal status reached, clears `activeRunId`, calls `refetchLatest()`.

Trigger `onSuccess` sets `activeRunId = data.run_id` and `pollStartedAt = Date.now()`.

Duplicate submission prevention: Run button disabled while `activeRunId` is set.

UI states rendered:
| Run Status | Display |
|-----------|---------|
| PENDING | "Queued… — waiting to start…" |
| RUNNING | "Running…" (animated) |
| COMPLETED | Score + severity badge + "View report" |
| FAILED | Error message + "Retry" link |
| Timeout | Warning message + "Refresh" link |

### Browser Validation

Triggered run on module `ACX118G`:
- Immediately showed "Queued… — waiting to start…"
- After ~8s showed completed score + "View report"
- Run button disabled during polling
- No duplicate submission possible

---

## B9: Accreditation-to-Findings Gap Promotion

### New Service

**`backend/app/services/gap_promotion_service.py`**

Converts accreditation readiness gaps into operational `AuditFinding` records.

**Duplicate prevention key**: `(institution_id, module_id, finding_type, title[:120])` where existing finding is not in `{RESOLVED, CLOSED}`.

**Result categories**:
- `promoted`: new finding IDs created
- `linked`: existing active finding IDs (no duplicate)
- `skipped`: gap titles where a linked finding already existed
- `errors`: per-gap error messages

**RBAC**: QA Officer or above only.

### New Endpoint

`POST /api/v1/accreditation-readiness-audits/{run_id}/promote-gaps`

- Body: `{gap_finding_ids: [uuid, ...] | null}` — null promotes all gaps
- Returns: `{promoted, linked, skipped, errors}`
- 403 if not QA Officer+, 404 if run not found, 409 if run not completed

### Security

- Tenant check: `run.institution_id == actor.institution_id` (SYSTEM_ADMIN bypasses)
- Requires completed run — cannot promote from in-flight run
- Each new finding gets `FindingStatusHistory` entry with promotion note
