# ADR-0003 — Tshwane University of Technology as Pilot Institution

**Status:** Accepted  
**Date:** 2026-06-25  
**Deciders:** Phase 5.4B design session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

AQAA requires a real-world institution for its first live pilot. The pilot institution must:

1. Have publicly accessible, official academic data (to avoid reliance on internal access)
2. Have a clear, well-bounded academic structure suitable for a phased pilot
3. Represent South African higher education authentically (CHE, DHET, SAQA, NQF)
4. Have a distinctive programme offering that demonstrates AQAA's domain coverage

---

## Decision

**Tshwane University of Technology (TUT)** is selected as the first pilot institution for AQAA.

**Pilot scope:** Faculty of Information and Communication Technology (ICT) — 4 departments, 25 programmes (NQF 6–10).

The pilot uses only data verifiable from official TUT sources (`tut.ac.za`, `tsb.ac.za`). Data from secondary websites (briefly.co.za, studychoices.org.za, etc.) is documented but not loaded until officially confirmed via PDF extraction.

The TUT pilot runs alongside the existing GFU/RCT demo data, which is preserved until the TUT pilot is fully operational.

---

## Consequences

### Positive
- TUT is one of South Africa's largest universities (60,000+ students, 7 faculties)
- TUT's Faculty of ICT is the only standalone ICT faculty in South Africa — a distinctive, well-documented scope
- All required data is publicly available at tut.ac.za (official HTML + PDF prospectuses)
- TUT's programme structure (HC → Diploma → Adv Diploma → PGDip → Masters → Doctorate) demonstrates AQAA's full NQF range
- Engineering faculty is the largest in South Africa — strong future expansion potential
- TUT uses CHE/DHET/SAQA/ECSA — covers all major SA QA frameworks

### Negative
- ICT Prospectus PDF is binary-encoded — requires `pdfminer.six` installation before module-level data can be loaded
- Some data (APS requirements, credits) sourced from secondary sites initially — requires PDF verification
- Contact with TUT directly would be needed for real deployment (access to internal QA documents)

### Neutral
- TUT data is loaded as a separate tenant (`institution.code = "TUT"`)
- GFU/RCT demo data preserved in parallel until TUT pilot validated
- Phase 5.4E loads the verified 34-record pilot (1 institution, 3 campuses, 1 faculty, 4 departments, 25 programmes)
- Module-level data deferred until PDF extraction complete

---

## Alternatives Considered

### Alternative 1 — University of Pretoria (UP)
Well-known traditional university with large programme catalogue.

**Deferred:** UP's website does not provide programme data in as structured a format as TUT's faculty-specific pages. TUT's ICT faculty pages provide department names, programme names, and NQF levels explicitly in HTML — reducing reliance on PDF extraction for initial pilot. UP deferred for Phase 5.6.

### Alternative 2 — UNISA
Distance education university with 3,000+ modules.

**Deferred:** UNISA's scale is appropriate for a mature platform but creates excessive complexity for a pilot. UNISA deferred for Phase 7+.

### Alternative 3 — Cape Peninsula University of Technology (CPUT)
Similar profile to TUT.

**Deferred:** TUT was selected first due to its ICT faculty's unique distinction. CPUT planned for Phase 5.6.

### Alternative 4 — Custom Fictional Institution
Create a fictional institution for piloting rather than using real data.

**Rejected:** GFU and RCT already serve this purpose (demo data). The pilot must use real data to validate that AQAA can handle actual SA institutional structures, official NQF levels, real APS requirements, and authentic academic hierarchies.

---

## Implementation Notes

- TUT IKP: `ikp/institutions/tut/2026/v1.0.0/`
- Seed script: `database/seed_data/seed_tut.py` (to be created in Phase 5.4E)
- ICT Prospectus PDF: already downloaded during Phase 5.4B — requires `pdfminer.six` for extraction
- Official sources confirmed: 4 department pages at `tut.ac.za/ict/{dept}/`

---

## References

- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0003
- `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md` — TUT Pilot IKP
- Phase 5.4B research report (session context)
- Phase 5.4C IKP Architecture document (session context)
