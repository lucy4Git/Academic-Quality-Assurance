# AQAA Accreditation-to-Findings Integration (B9)

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B9)  

---

## Purpose

Bridge accreditation readiness gaps (low-priority readiness flags) and the operational findings lifecycle (tracked corrective actions). Gaps from a completed accreditation run can be promoted to `AuditFinding` records so they enter the full 12-status workflow with assignment, deadlines, and audit trails.

---

## Flow

```
1. QA Officer triggers accreditation readiness audit
   POST /accreditation-readiness-audits/modules/{module_id}/trigger

2. Run completes (polled via GET /{run_id})

3. QA Officer reviews gaps in the report
   GET /{run_id}/report

4. QA Officer promotes selected gaps (or all) to operational findings
   POST /{run_id}/promote-gaps
   Body: {gap_finding_ids: [uuid, ...]}  // null = all

5. Response categorises each gap:
   - promoted: new AuditFinding created, status=OPEN
   - linked: existing active finding already exists (no duplicate)
   - skipped: title included in linked set
   - errors: gap-level failures

6. Promoted findings enter normal workflow:
   OPEN → ACKNOWLEDGED → ASSIGNED → IN_PROGRESS → RESOLUTION_SUBMITTED → UNDER_REVIEW → RESOLVED
```

---

## Duplicate Prevention

Before creating a new finding, the service searches for an existing **active** (non-RESOLVED, non-CLOSED) finding with:

```sql
institution_id = run.institution_id
AND module_id = run.module_id
AND finding_type = gap.finding_type
AND status NOT IN ('resolved', 'closed')
AND title ILIKE '{gap.title[:120]}%'
```

If found: records as `linked`, skips creation.  
If not found: creates new `AuditFinding` with title prefix `[Accreditation Gap]`.

This prevents repeated accreditation runs from flooding the findings backlog with duplicates.

---

## Promoted Finding Structure

```python
AuditFinding(
    audit_run_id=run_id,               # source accreditation run
    finding_type=gap.finding_type,
    severity=gap.severity,
    document_category=gap.document_category,
    title=f"[Accreditation Gap] {gap.title}",
    description=gap.description,
    recommendation=gap.recommendation,
    status=FindingStatus.OPEN,
    is_resolved=False,
)
FindingStatusHistory(
    from_status=None,
    to_status=FindingStatus.OPEN,
    note=f"Promoted from accreditation readiness run {run_id} by {actor.email}.",
)
```

---

## RBAC

| Action | Minimum Role |
|--------|-------------|
| Trigger accreditation audit | PROGRAMME_COORDINATOR |
| View report / gaps | Any authenticated user (same institution) |
| Promote gaps to findings | QUALITY_ASSURANCE_OFFICER |

---

## Implementation Files

| File | Role |
|------|------|
| `backend/app/services/gap_promotion_service.py` | Core promotion logic |
| `backend/app/routes/accreditation_readiness_audits.py` | `POST /{run_id}/promote-gaps` endpoint |
