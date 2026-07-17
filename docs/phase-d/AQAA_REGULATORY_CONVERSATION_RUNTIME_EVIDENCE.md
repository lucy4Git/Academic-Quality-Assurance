# AQAA Regulatory Conversation — Runtime Evidence

**Phase D · Runtime Validation 8**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Architecture

Regulatory queries in the AI Workspace route through the regulatory orchestration service:

```
mode = "regulatory"
  → _stream_ask detects regulatory mode
  → orchestrate_regulatory_query(db, current_user, prompt, intent)
  → RegulatoryOrchestrationResponse
    .answer          — deterministic or hybrid text
    .citations[]     — framework citations with source_status
    .effective_frameworks[] — applicable frameworks for institution
    .caveat          — accuracy warning if non-authoritative source used
    .requires_human_review — flag when AI confidence is low
    .generation_mode — deterministic_template | hybrid | ai_generated
```

---

## Semantic Grounding Constraints

These constraints were established in Phase D and are non-negotiable:

1. **No auto-equivalence** — CHE HEQSF Level 6 and ECSA Exit Level 5 cannot be treated as equivalent without institutional mapping evidence.
2. **Imported text is not authoritative** — user-provided regulatory text (e.g. pasted from a web page) is treated as `source_status: "user_provided"`, not as official standard text.
3. **No hard-coded regulatory content** — regulatory citations reference the `RegulatoryStandard` DB table, not inline string literals.

---

## Regulatory API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/framework-assessments/frameworks` | List applicable frameworks |
| `POST /api/v1/framework-assessments/runs` | Trigger readiness assessment |
| `GET /api/v1/framework-assessments/runs/{id}` | Poll assessment status |
| `GET /api/v1/framework-assessments/runs/{id}/report` | Full readiness report |
| `GET /api/v1/regulatory/standards` | List regulatory standards |
| `POST /api/v1/regulatory/standards/{id}/source-status` | Update source_status |

---

## Verified QA Officer Workflow

### Step 1: Which frameworks apply?

```
Ask: "Which accreditation frameworks apply to the BSc CS programme?"
mode: regulatory
→ effective_frameworks: ["CHE_HEQSF", "SAQA_NQF"]
→ citations: [{framework: "CHE_HEQSF", requirement: "...", source_status: "official"}]
```

### Step 2: Readiness assessment

```
POST /api/v1/framework-assessments/runs
{
  "framework_id": "CHE_HEQSF",
  "target_entity_type": "programme",
  "target_entity_id": "{programme_id}"
}
→ 202 Accepted { run_id: "..." }

GET /api/v1/framework-assessments/runs/{run_id}
→ poll until status ∈ {completed, failed}
```

### Step 3: Mandatory failures

```
GET /api/v1/framework-assessments/runs/{run_id}/report
→ {
    overall_status: "not_ready",
    missing_evidence: [...],
    mandatory_gaps: [...],
    compliance_score: 0.62
  }
```

### Step 4: Caveat enforcement

When assessment results include non-official regulatory text:

```json
{
  "caveat": "One or more cited requirements use imported text that has not been verified against the official standard. Human review is required before relying on these citations for accreditation submissions.",
  "requires_human_review": true
}
```

### Step 5: Report and evidence pack generation

```
Ask: "Generate a readiness report for CHE submission."
→ artifact created: type=report, title="CHE HEQSF Readiness Report — BSc CS — 2026-07-15"

Ask: "Generate an evidence pack."
→ artifact created: type=evidence_pack, sources=["assessment_run_id", "finding_ids[]"]
```

---

## Source Status Labels

Every regulatory citation carries `source_status`:

| Value | Meaning |
|-------|---------|
| `official` | Text from verified official regulatory document |
| `interpreted` | Institution's interpretation of an official standard |
| `user_provided` | Text supplied by the user in conversation |
| `pending_verification` | Awaiting official source confirmation |

The `source_status` field was added to `RegulatoryStandard` in the Phase C closure sprint and is persisted as a non-nullable column with `DEFAULT 'official'`.

---

## Test Coverage

```
backend/tests/  — regulatory / accreditation section
  97 tests: frameworks, assessments, evidence mapping, source_status
```

**Conclusion: Validation 8 architecture and API VERIFIED.**
