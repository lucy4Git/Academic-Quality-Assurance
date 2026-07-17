# AQAA Accreditation Readiness Scoring Specification

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B8)  

---

## Overview

The Accreditation Readiness agent is a meta-audit that invokes 6 compliance sub-agents and synthesises their results into a two-component readiness score.

---

## Component 1: Document Completeness Score (DCS)

Measures the fraction of required documents present and in `ready` upload state.

```
DCS = (documents_present / total_required) × 100
```

- `total_required`: count of all mandatory document categories for the module's programme level
- `documents_present`: count of files with `upload_state = 'ready'` in required categories
- Range: 0–100
- Weight: **60%** of composite score

---

## Component 2: Process Compliance Score (PCS)

Measures how many of the 6 sub-agent audits returned `compliant` or `needs_attention` (rather than `non_compliant` or `critical`).

```
PCS = (passing_agents / 6) × 100
```

Passing threshold per agent: `audit_status ∈ {compliant, needs_attention}`

Sub-agents included:
1. Assessment Compliance
2. Moderation Compliance
3. Attendance Compliance
4. Evidence Verification
5. Outcome Alignment
6. (Module Folder Audit — used for document presence, not scored separately)

Weight: **40%** of composite score

---

## Composite Accreditation Readiness Score (ARS)

```
ARS = (DCS × 0.60) + (PCS × 0.40)
```

---

## Risk Level Bands

| ARS Range | Risk Level | Audit Status |
|-----------|------------|--------------|
| 85–100 | Low | `compliant` |
| 70–84 | Medium | `needs_attention` |
| 50–69 | High | `non_compliant` |
| 0–49 | Critical | `critical` |

---

## Report Structure (`AccreditationReadinessReport`)

```json
{
  "run_id": "uuid",
  "module_id": "uuid",
  "composite_score": 72.5,
  "document_completeness_score": 80.0,
  "process_compliance_score": 60.0,
  "risk_level": "medium",
  "audit_status": "needs_attention",
  "sub_agent_breakdown": [
    {"agent": "assessment_compliance", "status": "compliant", "score": 90},
    ...
  ],
  "evidence_pack_completeness": {
    "present": 8,
    "missing": 4,
    "total_required": 12
  },
  "gaps": [...],
  "recommendations": [...],
  "completed_at": "2026-07-13T..."
}
```

---

## Gap Definition

A gap is any finding from any sub-agent with `audit_status ∈ {non_compliant, critical}` that represents a missing or defective evidence item. Gaps are candidates for promotion to operational `AuditFinding` records via the B9 `promote-gaps` endpoint.

---

## Scoring Notes

- Scores are computed at report generation time (`GET /{run_id}/report`), not stored as columns
- Individual finding severity does not directly affect the ARS — only pass/fail per agent and document presence
- A module with 0 documents uploaded scores DCS=0, ARS=0 regardless of process compliance
