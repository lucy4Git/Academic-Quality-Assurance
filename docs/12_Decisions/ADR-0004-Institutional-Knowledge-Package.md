# ADR-0004 — Institutional Knowledge Package (IKP) Architecture

**Status:** Accepted  
**Date:** 2026-06-29  
**Deciders:** Phase 5.4C architecture session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

Phase 5.4A (Database Provenance Audit) revealed that the AQAA database contained records of unknown origin:

- 5 institutions (only 2 seeded by scripts — 3 unknown origin)
- 11 faculties (only 8 seeded — 3 unknown origin)
- 22 programmes (only 16 seeded — 6 unknown origin)
- 83 users (only ~52 seeded — ~31 unknown origin)

These records were created via the API during feature testing without documentation. In an academic QA context, data of unknown provenance is unacceptable — incorrect NQF levels, APS requirements, or programme names would corrupt compliance calculations.

Additionally, Phase 5.4B revealed that TUT programme data from secondary websites (briefly.co.za, studychoices.org.za) differed from or contradicted official TUT sources. Loading unverified secondary data risked institutional trust in the platform.

A formal knowledge management architecture was needed that enforces provenance, versioning, confidence scoring, and controlled loading of all institutional data.

---

## Decision

All institutional data loaded into AQAA must pass through an **Institutional Knowledge Package (IKP)**.

The IKP is a version-controlled, provenance-tagged JSON package organised into 8 layers:
1. Institution Layer
2. Academic Structure Layer
3. Curriculum Layer
4. Quality Assurance Layer
5. Qualification Layer
6. Institutional Policy Layer
7. AI Knowledge Layer
8. Metadata and Versioning Layer

**Mandatory IKP rules:**
- Every knowledge object carries a provenance envelope (source URL, source type, extraction date, confidence score, verifier)
- Confidence scores below 0.85 from official sources are blocked from loading
- Confidence scores below 0.70 from any source are quarantined
- All IKP versions are preserved (immutable once sealed)
- New institutions are onboarded via IKP without requiring source code changes

**IKP file location:** `ikp/institutions/{code}/{year}/v{version}/`

---

## Consequences

### Positive
- All AQAA institutional data is traceable to its authoritative source
- Incorrect or unverified data is blocked at the ingestion gate
- Historical versions preserved — audit trail of what AQAA knew at any given time
- Multi-institution support requires only new IKP packages, not code changes
- AI agents can cite their data sources with confidence scores
- Data quality improves over time as confidence scores are updated from official sources

### Negative
- Loading new institution data now requires a multi-step pipeline (discover → extract → validate → score → review → assemble → import) instead of direct API insertion
- Existing GFU/RCT demo data predates the IKP — must remain as is or be retroactively packaged
- Phase 5.4E is blocked until ICT Prospectus PDF is extracted (credits, APS not confirmed)

### Neutral
- `knowledge_gap` tracking table required in AQAA database (to be added in Phase 5.4E migration)
- Human review queue required for fields scoring 0.70–0.84
- IKP management UI planned for Phase 6

---

## Alternatives Considered

### Alternative 1 — Direct API Import with Source Tagging
Add a `source_url` column to each entity and require it on creation via API.

**Rejected because:** A single source URL is insufficient. Provenance requires: source type, extraction date, confidence score, verifier, field-level attribution, page number, verbatim quote. A full provenance model cannot be collapsed to a single column. Furthermore, API-level insertion still allows low-confidence data to reach the database.

### Alternative 2 — Spreadsheet Import with Validation
Define a canonical spreadsheet template that institutions fill in, with validation rules.

**Rejected because:** Spreadsheets cannot carry field-level provenance. Data entered by institution staff cannot be verified against official sources. A TUT administrator entering APS values into a spreadsheet has no audit trail back to the official prospectus. The IKP JSON format is machine-parseable and provenance-aware in a way spreadsheets cannot be.

### Alternative 3 — Direct Database Seeding from Web Scraping
Automated web scraper that populates the database directly.

**Rejected because:** This produces exactly the problem described in the context — unverified, undocumented data of uncertain confidence. Scraping without provenance tracking or confidence scoring creates data that cannot be audited. The IKP pipeline adds confidence scoring and human review as a mandatory gate.

---

## Implementation Notes

IKP JSON schema is defined in `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md`.

Key schema constraint: every entity object must include a `provenance` object with all mandatory fields. The ingestion script validates this before loading.

Confidence score formula:
```
base = source_type_weight × extraction_quality_weight
source_type_weight: official_html=1.00, official_pdf=0.92, secondary=0.45
```

---

## References

- `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md` — Full IKP specification
- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0004
- `ikp/institutions/tut/2026/v1.0.0/` — TUT pilot IKP
