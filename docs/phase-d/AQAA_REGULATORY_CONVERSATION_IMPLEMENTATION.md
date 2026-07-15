# AQAA Regulatory Actions through Conversation

**Phase D9 · Regulatory and Accreditation Actions via AI Workspace**
**Date:** 2026-07-15

---

## Architecture

Regulatory and accreditation actions are dispatched through the orchestration registry. The assistant detects regulatory intent and routes through `request_planner` → `orchestration_registry.dispatch()` → Phase C services.

---

## Supported Regulatory Workflows

### Framework Citation
**Prompt:** "What HEQSF level applies to this module?"

- Intent: `REGULATORY_QUERY`
- Service: Phase C framework service (read-only)
- Response: structured block with framework name, level, citation URL, source_status
- **No hallucination:** only returns frameworks that are stored in the regulatory knowledge base
- **Source status shown:** `[VERIFIED]` | `[PROVISIONAL]` | `[UNVERIFIED]` label on each citation

### Standards Alignment Check
**Prompt:** "Is this module's assessment plan aligned with HEQSF standards?"

- Intent: `STANDARDS_ALIGNMENT`
- Route: outcome alignment agent trigger → waits for result
- Response: alignment percentage, gap list, cited standard
- **Cannot mark two standards as equivalent without human verification**

### Accreditation Readiness Query
**Prompt:** "What is our accreditation readiness status for this programme?"

- Intent: `ACCREDITATION_READINESS`
- Route: accreditation readiness audit agent
- Response: readiness percentage, missing evidence, action items

### Generate Accreditation Evidence Summary
**Prompt:** "Generate an accreditation evidence summary for this programme."

- Intent: `GENERATE_EVIDENCE_SUMMARY`
- Requires confirmation (generates artifact)
- Creates `AiArtifact` with `artifact_type = "accreditation_evidence_summary"`
- Content: structured evidence list by requirement, with upload_state for each file
- **Only includes files with `upload_state = "ready"`** — quarantined files excluded
- **[TEST FIXTURE] label added** if evidence is seeded test data

### Regulatory Gap Analysis
**Prompt:** "Run a regulatory gap analysis for CSC401."

- Intent: `REGULATORY_GAP_ANALYSIS`
- Requires confirmation
- Route: evidence verification agent
- Artifact generated: `artifact_type = "regulatory_gap_analysis"`

### Submit for Accreditation Review
**Prompt:** "Submit this programme for accreditation review."

- Intent: `SUBMIT_ACCREDITATION`
- Requires confirmation (+ QA Officer role)
- Route: accreditation readiness audit trigger
- Action: `AuditRun` created, status → 202 accepted, `run_id` returned

---

## Constraints

### Do Not Hard-Code Regulatory Standards
The assistant does NOT embed regulatory texts verbatim in its responses. It cites by name and version:
- ✅ "HEQSF Level 6 (SAQA, 2013 revision)"
- ❌ Reproducing full standard text

### No Automatic Equivalence Claims
The assistant cannot mark two regulatory standards as legally equivalent without a QA Officer explicitly recording a human verification event. Equivalence suggestions require confirmation and are stored as `PROVISIONAL` until signed off.

### Imported Text not Auto-Authoritative
Documents uploaded by users are not automatically treated as authoritative regulatory sources. They remain at `source_status = "imported"` until a QA Officer reviews and promotes them to `"verified"`.

### Confidential Evidence Protection
System Administrators do NOT automatically receive access to confidential evidence documents through conversational queries. Access follows the RBAC model — evidence is only returned to users with appropriate role AND programme/module ownership.

---

## Source Status Display
Every regulatory citation in AI responses includes a source status badge:

| Status | Display | Meaning |
|--------|---------|---------|
| `verified` | `[VERIFIED]` | Human-reviewed and signed off |
| `provisional` | `[PROVISIONAL]` | AI-suggested, pending human review |
| `unverified` | `[UNVERIFIED]` | Imported, not reviewed |
| `imported` | `[IMPORTED]` | System-ingested raw text |

---

## Pass/Fail Summary
| Check | Result |
|-------|--------|
| Framework citation with source_status | ✅ |
| No hallucinated regulatory text | ✅ |
| Standards alignment via agent | ✅ |
| Accreditation readiness via agent | ✅ |
| Evidence summary artifact created | ✅ |
| Quarantined files excluded | ✅ |
| Test fixture data labelled | ✅ |
| No auto-equivalence claims | ✅ |
| No auto-authoritative import | ✅ |
| QA Officer required for submission | ✅ |
| Tenant isolation enforced | ✅ |
