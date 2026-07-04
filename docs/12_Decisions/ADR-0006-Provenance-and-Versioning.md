# ADR-0006 — Provenance and Versioning for All Knowledge Objects

**Status:** Accepted  
**Date:** 2026-06-29  
**Deciders:** Phase 5.4C architecture session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

Academic quality assurance generates regulated data — compliance reports may be used in CHE accreditation submissions, SAQA qualification reviews, and institutional governance processes. If a QA report contains incorrect data (wrong NQF level, incorrect APS, outdated credit count), the institution could make regulatory submissions based on false information.

Additionally, AQAA will accumulate years of audit history, changing institutional data (annual prospectus updates), and evolving AI rules. Without a versioning system, it would be impossible to answer:

- "What did AQAA believe about this programme when this audit was conducted in 2025?"
- "When did the APS requirement for this programme change?"
- "Who verified this NQF level, and from what source?"

These are not optional features — they are fundamental to operating an auditable academic compliance platform.

---

## Decision

**Every knowledge object in AQAA must carry a provenance record and belong to a versioned IKP.**

### Provenance Requirements

Every field of every institutional knowledge record must be traceable to:
- The source type (official HTML, official PDF, etc.)
- The source URL
- The source document title
- The extraction date
- The extraction method
- The confidence score (0.0–1.0)
- The verifier (if human-verified)
- The effective date and expiry date

Fields without provenance must not be loaded into the AQAA database.

### Versioning Requirements

Institutional knowledge is version-controlled at the IKP level using semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: new academic year
- MINOR: new data added (e.g., PDF extraction completing)
- PATCH: corrections to existing data

Sealed IKP versions are immutable. No historical version is ever deleted.

### Confidence Scoring

Every field has a confidence score:
- ≥ 0.85: auto-approved, loads immediately
- 0.70–0.84: flags for human review, loads with `pending_review` status
- < 0.70: quarantined, does not load

---

## Consequences

### Positive
- All AQAA data is fully auditable — any value can be traced to its source
- Historical queries are possible: "what did AQAA know in 2025?"
- AI transparency: agents can cite the confidence of their data inputs
- Regulatory defensibility: compliance reports cite source data with provenance
- Year-on-year trend analysis is possible (compare IKP v1.0 with v2.0)

### Negative
- Every knowledge object requires significantly more metadata than a simple database row
- Loading institutional data is a multi-step process, not a direct import
- Human review queue must be processed for medium-confidence items
- Storage grows substantially (all versions preserved)

### Neutral
- `provenance_records` table required in AQAA database
- `knowledge_gaps` tracking table required (fields blocked from loading)
- IKP file store required (`ikp/institutions/`) alongside the database

---

## Alternatives Considered

### Alternative 1 — No Versioning (Always Current)
Only store the current version of institutional data. Updates overwrite previous values.

**Rejected because:** Overwrites destroy audit trail. If a programme's NQF level is incorrectly entered as 6 and later corrected to 7, there would be no record of when the correction was made, who made it, or what audit runs were affected. In a regulatory context, this is unacceptable.

### Alternative 2 — Git-Based Versioning
Use Git to track changes to institutional data files.

**Partially accepted:** The IKP file store does use Git-friendly JSON files that can be committed to version control. However, the database also needs versioning at the row level — Git alone cannot provide per-field confidence scoring or human review queues. The two systems are complementary.

### Alternative 3 — Audit Logs Only (No Forward Versioning)
Log all changes to data (who changed what and when) but don't maintain full versions.

**Rejected because:** Audit logs record what changed, but not why — and not the full state at any given time. Reconstructing "what AQAA knew in 2025" from audit logs would require replaying all changes from the beginning. Full version snapshots (IKP packages) are much more efficient for this use case.

---

## Implementation Notes

Provenance record schema (minimum required fields):
```json
{
  "source_type": "official_html | official_pdf | official_email | manual_verified | heqsf_standard | secondary_unverified",
  "source_url": "https://...",
  "source_document": "...",
  "page_number": null,
  "extraction_method": "web_fetch_automated | pdf_text_extract | ocr | manual_entry",
  "extraction_date": "YYYY-MM-DD",
  "extracted_by": "...",
  "verified_by": null,
  "confidence_score": 0.0,
  "version": "1.0.0",
  "effective_date": "YYYY-MM-DD",
  "expiry_date": null,
  "status": "active | pending_review | superseded | quarantined",
  "last_reviewed": "YYYY-MM-DD"
}
```

---

## References

- `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md` — Sections 6 (Provenance) and 7 (Versioning)
- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0004, DEC-0007
- `docs/12_Decisions/ADR-0004-Institutional-Knowledge-Package.md`
