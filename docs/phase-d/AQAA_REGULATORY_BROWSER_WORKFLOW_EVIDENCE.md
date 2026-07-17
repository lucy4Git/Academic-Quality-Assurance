# AQAA Phase D — Regulatory Browser Workflow Evidence

**Phase D · Browser Acceptance Test**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Regulatory Conversation Workflow

Regulatory conversations allow QA Officers and Coordinators to query against South African higher education regulatory frameworks (CHE HEQSF, DHET, SAQA, industry-specific standards).

---

## Regulatory Modes Verified (HTTP API)

### Framework Query

```
POST /api/v1/ai-assistant/ask-stream
{
  "query": "What are the CHE HEQSF requirements for assessment moderation?",
  "institution_code": "TUT"
}
```

**Response characteristics verified:**
- `source_status` label on each citation (`active`, `draft`, `superseded`) ✅
- No auto-equivalence assertion between CHE and DHET standards ✅
- Caveats inserted when citing `draft` or `superseded` sources ✅
- Imported text is not treated as authoritative without a `source_status` ✅

### Gap Analysis

```
POST /api/v1/ai-assistant/ask-stream
{
  "query": "Identify gaps between TUT's assessment policy and CHE HEQSF Section 7",
  "institution_code": "TUT"
}
```

**Response characteristics verified:**
- Gap findings expressed as conditional statements, not assertions ✅
- Source references include document name + version ✅
- No fabrication of regulatory requirements ✅

### Accreditation Readiness

```
POST /api/v1/ai-assistant/ask-stream
{
  "query": "What is the accreditation readiness status for the Computing programme?",
  "institution_code": "TUT"
}
```

**Response characteristics verified:**
- References actual audit run data (not invented findings) ✅
- Audit run status (`completed`, `in_progress`) displayed ✅
- Suggests evidence upload for missing documentation ✅

---

## Source Status Labels

All regulatory citations include a `source_status` field in the response:

| Status | Meaning | Display in UI |
|--------|---------|--------------|
| `active` | Current, authoritative | Green badge |
| `draft` | Under review | Yellow badge + caveat |
| `superseded` | Replaced by newer version | Orange badge + warning |
| `null` | Status unknown | No badge |

Verified in `AQAA_REGULATORY_CONVERSATION_RUNTIME_EVIDENCE.md`.

---

## Anti-Hallucination Guards

The regulatory conversation engine enforces:

1. **No auto-equivalence** — CHE HEQSF and SAQA NQF standards are never treated as identical unless explicitly cross-referenced in a source document
2. **Imported text caveat** — Text pasted into the chat is annotated as "user-provided content, not verified against institutional records"
3. **Framework specificity** — Queries about "the regulations" always resolve to a named framework, never generic
4. **Source attribution** — All regulatory claims include a source document reference

These are enforced in the request planner and context engine, verified in `TestRegulatoryCaveats` (unit tests). ✅

---

## Artifact Generation from Regulatory Conversations

Regulatory conversations can produce artifacts:
- Gap analysis report → `AiArtifact` with `type: report`
- Evidence pack checklist → `AiArtifact` with `type: evidence_pack`
- Corrective Action Plan → `AiArtifact` with `type: cap`

Artifacts are accessible in the right panel (Artifacts tab) after creation. Export in JSON and Markdown verified. ✅

---

**Conclusion: Regulatory conversation workflow VERIFIED.** Source status labels, anti-hallucination guards, framework specificity, and artifact generation all confirmed.
