# Research Documentation

This section contains research reports, institutional data investigations, and knowledge collection outputs.

## Contents

| Document | Date | Status | Description |
|----------|------|--------|-------------|
| `TUT_5.4A_PROVENANCE_AUDIT.md` | 2026-06-29 | ✅ Complete | Database provenance audit — all existing records traced to source |
| `TUT_5.4B_KNOWLEDGE_COLLECTION.md` | 2026-06-29 | ✅ Complete | Official TUT academic data collection (7 faculties, 35 depts, 200+ programmes) |
| `TUT_5.4C_SOURCE_REVIEW.md` | 2026-06-29 | ✅ Complete | Source classification, secondary data flagging, ICT pilot dataset |

## Phase 5.4 Research Outputs Summary

### 5.4A — Database Provenance Audit
- **Finding:** 3 institutions, 3 faculties, 6 programmes, 31 users of unknown origin
- **Cause:** Manual API testing without documentation
- **Resolution:** IKP architecture introduced (Phase 5.4C)

### 5.4B — TUT Knowledge Collection
- **Institutions researched:** TUT (Tshwane University of Technology)
- **Official sources used:** tut.ac.za (HTML), tsb.ac.za, online.tut.ac.za
- **Secondary sources identified but not loaded:** briefly.co.za, studychoices.org.za, apply.org.za
- **Pilot scope:** Faculty of ICT — 4 departments, 25 programmes (NQF 6–10)

### 5.4C — Source Review
- **Confirmed from official sources:** 1 institution, 3 campuses, 1 faculty, 4 departments, 25 programme names, all NQF levels
- **Not confirmed (pending PDF):** credits, APS, admission requirements, extended curriculum variants, all modules
- **Next step:** `pdfminer.six` extraction of `Part6_ICT_Prospectus.pdf`

## Naming Convention

Research documents are named: `[INSTITUTION]_[PHASE]_[TOPIC].md`  
Example: `TUT_5.4B_KNOWLEDGE_COLLECTION.md`
