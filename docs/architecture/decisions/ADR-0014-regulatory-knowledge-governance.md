# ADR-0014 — Regulatory Knowledge Governance Model

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

AQAA's AI Workspace cites regulatory documents. The accuracy and authority of these citations directly determines the trustworthiness of the platform for QA Officers and institutional accreditation work. The governance model must answer:

1. Who is authorised to add a document as `OFFICIAL_VERIFIED`?
2. How is a document's authenticity verified before indexing?
3. What happens when a document is updated or superseded?
4. How are institutions' own policies distinguished from national frameworks?

---

## Decision

**Two-tier governance model: National (AQAA Engineering operator-controlled) and Institutional (institution System Admin-controlled).**

### Tier 1 — National Regulatory Documents (OFFICIAL_VERIFIED)

**Authority:** AQAA Engineering only. No institution user can elevate a document to `OFFICIAL_VERIFIED`.

**Verification procedure:**
1. Document downloaded from the issuing body's official website (CHE, DHET, SAQA, etc.)
2. Download URL, document title, version, and download date recorded in `regulatory_document_registry`
3. SHA-256 hash of the downloaded PDF recorded as `document_hash`
4. An AQAA Engineering engineer reviews the document metadata against the issuing body's published document catalogue
5. Ingestion approved in writing (Slack message / email) by a second AQAA Engineering team member
6. Document indexed with `source_status = OFFICIAL_VERIFIED`

**Change control:**
- When a new version of a national document is released, the old document's `source_status` is set to `SUPERSEDED` with `superseded_by` pointing to the new record
- Superseded documents are excluded from new queries by default
- A banner in the AI Workspace alerts the System Admin when superseded documents exist that have not been replaced

**Annual review:** All OFFICIAL_VERIFIED documents are reviewed annually (July) against the issuing body's website. Documents with broken source URLs are flagged as `SUPERSEDED` until re-sourced.

### Tier 2 — Institutional Documents (INSTITUTIONAL_APPROVED)

**Authority:** Institution System Admin. No AQAA Engineering approval required.

**Verification procedure:**
- Institution System Admin uploads document via `/admin/regulatory-docs`
- System scans for viruses (ClamAV) and validates MIME type
- No content review by AQAA Engineering — the institution is responsible for document accuracy
- Document indexed with `source_status = INSTITUTIONAL_APPROVED` and scoped to `institution_id`
- Document visible only to users within that institution

**Limitations:**
- Institutional documents cannot be elevated to `OFFICIAL_VERIFIED` by any user
- Institutional documents are not included in AQAA Engineering's grounding coverage metric baseline (they are counted separately)

### Supersession State Machine

```
DRAFT_IMPORT → OFFICIAL_VERIFIED → SUPERSEDED → ARCHIVED
                    ↑
INSTITUTIONAL_APPROVED (parallel tier, not on this path)
```

- `DRAFT_IMPORT`: Registered but not yet verified or indexed
- `OFFICIAL_VERIFIED`: Verified, indexed, actively cited
- `SUPERSEDED`: Replaced by newer version; excluded from new queries
- `ARCHIVED`: Removed from Qdrant; record retained for audit trail only

### What This Does NOT Cover

- Permissions for which AI model can cite which documents — all indexed documents in the institution's scope are available for citation
- Automated crawling of regulatory body websites — all ingestion is operator-initiated
- ECSA, HPCSA, SACE (professional council frameworks) — governance model for these is identical but ingestion is deferred to Phase F

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
