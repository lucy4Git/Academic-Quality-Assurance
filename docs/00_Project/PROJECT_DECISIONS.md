# AQAA — Project Decision Log

**Document ID:** DEC-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

This log captures all significant project-level decisions. For architectural decisions, see `docs/12_Decisions/ADR-*.md`.  
This file records strategic, scope, and operational decisions that are not architecture-specific.

---

## Decision Format

Each decision entry uses this structure:

```
### DEC-XXXX — [Title]
- **Date:** YYYY-MM-DD
- **Status:** Active | Superseded | Reversed
- **Made by:** [Person or session]
- **Decision:** [What was decided]
- **Rationale:** [Why]
- **Impact:** [What changes as a result]
- **Supersedes:** [DEC-XXXX if applicable]
- **Superseded by:** [DEC-XXXX if applicable]
```

---

## Active Decisions

### DEC-0001 — AQAA Is a Standalone Project
- **Date:** 2026-06-11
- **Status:** Active — Non-negotiable
- **Made by:** Project initiation
- **Decision:** AQAA has no relationship to any other project on this machine or in this organisation, including MSc Academic Intelligence System, RIAE, Lecturer Support Agent, PersonalOS, Poultry MIS, or any other system.
- **Rationale:** AQAA is being developed as an independent commercial platform. Cross-project contamination would compromise its integrity as a deployable product.
- **Impact:** All code, data models, configurations, and documentation must be self-contained. No imports, borrowing, or adaptation from other projects.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0002 — Multi-Tenant Architecture
- **Date:** 2026-06-11
- **Status:** Active
- **Made by:** Architecture design session
- **Decision:** AQAA is a multi-tenant platform. Every institution is an isolated tenant. Data from one institution is never accessible to another without explicit System Admin access.
- **Rationale:** A single-tenant architecture would require separate deployments per institution, multiplying infrastructure costs and maintenance burden. Multi-tenancy allows a single platform to serve many institutions while maintaining strict data isolation.
- **Impact:** `institution_id` is required on all data records. All service-layer queries filter by `institution_id`. RBAC enforces tenant scope at the role level.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0003 — Tshwane University of Technology Selected as Pilot Institution
- **Date:** 2026-06-25
- **Status:** Active
- **Made by:** Phase 5.4B decision
- **Decision:** TUT is the first real-world institution to be onboarded into AQAA as a pilot. The pilot scope is the Faculty of ICT (4 departments, 25 programmes).
- **Rationale:** TUT has a well-documented, publicly available academic structure. Its Faculty of ICT is South Africa's only standalone ICT faculty, making it a distinctive and well-bounded pilot scope. Official data is available via tut.ac.za.
- **Impact:** A TUT IKP is being built. Demo data (GFU, RCT) is preserved. TUT will be loaded as a separate tenant once the ICT Prospectus PDF is extracted.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0004 — Institutional Knowledge Package (IKP) Architecture Introduced
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4C architecture session
- **Decision:** All institutional data loaded into AQAA must pass through an Institutional Knowledge Package (IKP). The IKP is the single source of truth for all institutional academic knowledge.
- **Rationale:** Untracked data imports led to uncertainty about data provenance (Phase 5.4A audit revealed 3 unexplained institutions, 3 unexplained faculties, 6 unexplained programmes, 31 unexplained users). The IKP enforces provenance, versioning, and confidence scoring before any data enters the database.
- **Impact:** New data loading pipeline required. Confidence scoring enforced (< 0.85 blocked). All future institutions must have an IKP before database import.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0005 — Documentation-Driven Development Adopted
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4D architecture session
- **Decision:** Every feature, subsystem, and architectural decision in AQAA must be documented before or concurrently with implementation. The `docs/` directory is a first-class project artefact.
- **Rationale:** The project has grown across multiple sessions. Without formal documentation, critical decisions (ShadCN `asChild` incompatibility, double-Depends() bug, Faculty tablename override) had to be rediscovered. Documentation prevents regressions and enables onboarding of new contributors.
- **Impact:** `CLAUDE_DEVELOPMENT_STANDARD.md` becomes the engineering constitution. Changelog, ADRs, and phase tracker are mandatory. No phase is closed without documentation update.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0006 — AI-First Hybrid Architecture
- **Date:** 2026-06-11
- **Status:** Active
- **Made by:** Architecture design session
- **Decision:** AQAA uses an AI-first hybrid architecture: AI agents automate pattern detection; human academic professionals retain authority over all final decisions.
- **Rationale:** Full AI automation of QA decisions is inappropriate in an academic regulatory context. However, manual-only processes do not scale. The hybrid model provides efficiency gains while preserving academic accountability.
- **Impact:** All AI audit routes return 202 (async) with a `run_id`. The UI never presents AI findings as final — always as recommendations requiring human review.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0007 — Secondary Source Data Must Not Be Loaded Without Official Verification
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4C data review
- **Decision:** Data sourced from secondary websites (briefly.co.za, studychoices.org.za, apply.org.za, etc.) must not be loaded into AQAA. Only data from official institutional sources (tut.ac.za, tsb.ac.za) or officially published PDF documents may be loaded.
- **Rationale:** Secondary sources may aggregate, approximate, or misrepresent official institutional data. In an academic QA context, incorrect data (wrong APS, wrong NQF level, wrong credits) would corrupt compliance calculations and damage institutional trust in the platform.
- **Impact:** IKP confidence threshold of 0.85 blocks secondary-sourced data. APS values for TUT/ICT remain unloaded until ICT Prospectus PDF is extracted.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0008 — Demo Data (GFU, RCT) Preserved Until TUT Pilot Validated
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4C recommendation
- **Decision:** The Greenfield University (GFU) and Riverside College of Technology (RCT) demo datasets are not deleted until the TUT pilot is fully operational and validated.
- **Rationale:** Demo data provides a stable test environment during TUT onboarding. Deleting it prematurely would leave the platform without test data during a transitional period.
- **Impact:** Three institutions will coexist in the database temporarily. GFU and RCT are clearly marked as demo data via seed scripts.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0011 — Academic Document Intelligence Platform (ADIP) Adopted
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4F architecture session
- **Decision:** AQAA will implement ADIP as its core document intelligence subsystem. ADIP replaces the originally planned PDF-only extraction script. ADIP is format-agnostic (30+ document types), provenance-aware (per-field source anchors), confidence-gated, multi-institution, and AI-ready.
- **Rationale:** A PDF-only script would accumulate format-specific technical debt as AQAA encounters DOCX, XLSX, PPTX, HTML, scanned PDFs, ZIP evidence packs, and future media formats. ADIP provides a unified, extensible architecture that handles all formats behind a common interface. The incremental delivery model (PDF first in Phase 5.4G) avoids over-engineering while preserving the correct long-term architecture.
- **Impact:** New `backend/app/adip/` Python package. New Alembic migration for ADIP registry tables. Phased implementation through Phase 8. ADR-0008 created.
- **Supersedes:** Planned "Phase 5.4G PDF extraction script" concept
- **Superseded by:** —

---

### DEC-0012 — ADIP Implemented Incrementally (Phase 5.4G First)
- **Date:** 2026-06-29
- **Status:** Active
- **Made by:** Phase 5.4F architecture session
- **Decision:** ADIP is designed in full (Phase 5.4F) but implemented incrementally. Phase 5.4G implements only PDF + HTML extraction (Layers 1–7, text + tables). Video/audio, full vector integration, and human review UI are deferred to Phase 7 and Phase 6 respectively.
- **Rationale:** The TUT pilot is blocked on extracting data from 6 downloaded PDFs. Building the full ADIP (15 layers, all formats) before extracting those PDFs would delay the pilot unnecessarily. The architecture is designed for the full scope; implementation is prioritised for the blocking need.
- **Impact:** Phase 5.4G scope is: pdfminer.six + camelot-py + TUT-specific mapper + IKP v1.1.0 assembly + seed_tut.py.
- **Supersedes:** None
- **Superseded by:** —

---

### DEC-0009 — SaaS Multi-Tenant Deployment Model Proposed
- **Date:** 2026-06-29
- **Status:** Proposed — Awaiting ADR
- **Made by:** Phase 5.4E product strategy session
- **Decision:** AQAA is proposed to deploy as a multi-tenant SaaS platform with tiered licensing: Pilot → Institutional → Consortium → National. Pricing models: per-user annual licence and consortium fee.
- **Rationale:** Multi-tenant architecture is already implemented. SaaS deployment allows a single platform to serve all 26 South African public universities without separate deployments. Recurring licence revenue supports ongoing development.
- **Impact:** Requires production infrastructure (cloud storage, SMTP, SSL, monitoring). Requires POPIA-compliant data processing agreements per institution. Requires ADR to formalise.
- **Supersedes:** None
- **Superseded by:** —
- **Note:** Requires new ADR before implementation begins.

---

### DEC-0010 — Open-Core Licensing Evaluation Deferred
- **Date:** 2026-06-29
- **Status:** Active — Deferred
- **Made by:** Phase 5.4E product strategy session
- **Decision:** Evaluation of an open-core licensing model (free community edition + paid enterprise) is deferred until Phase 8, after at least 3 institutions are operational on the platform.
- **Rationale:** Open-core licensing could accelerate national adoption, particularly among resource-constrained institutions. However, determining the feature boundary between free/paid requires understanding real institutional needs, which requires production experience.
- **Impact:** No immediate action. Review at start of Phase 8.
- **Supersedes:** None
- **Superseded by:** —

---

## Template for Future Decisions

```markdown
### DEC-XXXX — [Title]
- **Date:** YYYY-MM-DD
- **Status:** Active | Superseded | Reversed
- **Made by:** [Person or session identifier]
- **Decision:** [Clear statement of what was decided]
- **Rationale:** [Why this decision was made — context and constraints]
- **Impact:** [Concrete changes this decision requires]
- **Supersedes:** [DEC-XXXX or None]
- **Superseded by:** [DEC-XXXX or — if still active]
```

---

*Update this file whenever a significant project-level decision is made.*  
*For architecture-level decisions, also create a corresponding ADR.*
