# AQAA — Phase Tracker

**Document ID:** TRACK-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

---

## Status Key

| Symbol | Status |
|--------|--------|
| ✅ | Complete |
| 🔄 | In Progress |
| ⏳ | Planned |
| ⏸️ | Blocked |
| ❌ | Cancelled |

---

## Phase Registry

| Phase | Name | Status | Start Date | Completion Date | Dependencies | Owner | Notes |
|-------|------|--------|-----------|-----------------|-------------|-------|-------|
| 1 | Frontend Foundation | ✅ | 2026-06-11 | 2026-06-11 | None | Engineering | Next.js 14, auth, sidebar, RBAC middleware |
| 2C-1 | Institution Management | ✅ | 2026-06-11 | 2026-06-11 | Phase 1 | Engineering | |
| 2C-2 | Faculty Management | ✅ | 2026-06-11 | 2026-06-11 | 2C-1 | Engineering | |
| 2C-3 | Department Management | ✅ | 2026-06-11 | 2026-06-11 | 2C-2 | Engineering | |
| 2C-4 | Programme Management | ✅ | 2026-06-11 | 2026-06-11 | 2C-3 | Engineering | |
| 3A | Complete RBAC System | ✅ | 2026-06-11 | 2026-06-11 | Phase 1 | Engineering | |
| 3B | Programme QA Fields + Dashboard | ✅ | 2026-06-24 | 2026-06-24 | 2C-4, 3A | Engineering | |
| 3C | Module Management | ✅ | 2026-06-24 | 2026-06-24 | 3B | Engineering | |
| 3D | Academic Structure Verification | ✅ | 2026-06-24 | 2026-06-24 | 3C | Engineering | |
| 4A | Manual QA Audit Engine | ✅ | 2026-06-25 | 2026-06-25 | 3D | Engineering | ModuleAudit + AuditChecklistItem |
| 4B | Evidence Upload + File Library | ✅ | 2026-06-26 | 2026-06-26 | 4A | Engineering | AuditEvidence, storage backend |
| 4C | Evidence Preview + Audit History | ✅ | 2026-06-26 | 2026-06-26 | 4B | Engineering | AuditHistory, preview endpoint |
| 5 | Workflow Automation + Notifications | ✅ | 2026-06-29 | 2026-06-29 | 4C | Engineering | 9-state workflow, comments, notifications, approvals |
| 5.4A | Database Provenance Audit | ✅ | 2026-06-29 | 2026-06-29 | 5 | Engineering | Identified 3 unexplained institutions |
| 5.4B | TUT Academic Knowledge Collection | ✅ | 2026-06-29 | 2026-06-29 | 5.4A | Engineering | 25 ICT programmes verified |
| 5.4C | IKP Architecture Design | ✅ | 2026-06-29 | 2026-06-29 | 5.4B | Engineering | 12 architecture deliverables |
| 5.4D | Engineering Documentation Standard | ✅ | 2026-06-29 | 2026-06-29 | 5.4C | Engineering | 39 docs across 15 directories |
| 5.4E | Product Foundation & Enterprise Knowledge Framework | ✅ | 2026-06-29 | 2026-06-29 | 5.4D | Engineering | 5 master docs + 3 updates |
| 5.4F | ADIP Architecture Design | ✅ | 2026-06-29 | 2026-06-29 | 5.4E | Engineering | 15 docs + ADR-0008 |
| **5.4G** | **ADIP Implementation Foundation** | **✅** | **2026-06-29** | **2026-06-29** | **5.4F** | **Engineering** | **472 tests, pipeline ran, 24,573 chunks** |
| **5.4H** | **ADIP Table Extraction & TUT ICT Completion** | **✅** | **2026-07-01** | **2026-07-01** | **5.4G** | **Engineering** | **490 tests, 107 tables, 22 programmes, 174 modules** |
| **Sprint 1** | **Knowledge Review Centre + TUT DB Load** | **✅** | **2026-07-01** | **2026-07-01** | **5.4H** | **Engineering** | **532 tests, 11 endpoints, 3 pages, 196 AI chunks** |
| **Sprint RS-1** | **Demo User Deactivation + Pilot Access Control** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint 1** | **Engineering** | **629 tests, 82 users deactivated, 38 auth tests** |
| **Sprint RS-2** | **Archive Filter + Institution Stats** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint RS-1** | **Engineering** | **654 tests, archive filter on 5 endpoints, stats endpoint, split institutions view** |
| **Sprint RS-3** | **Pilot Dataset Repair + Institution Filters** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint RS-2** | **Engineering** | **654 tests, UP codes fixed, institution filter on 4 pages, InstitutionSelect component** |
| 5.4I | TUT ICT Pilot Database Load | ✅ | 2026-07-01 | 2026-07-01 | Sprint 1 | Engineering | seed_tut.py — requires Docker DB running |
| **Sprint 2** | **Qdrant Vector Indexing + Knowledge Search** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint RS-3** | **Engineering** | **700 tests, TUT 196 chunks indexed, UP 28 chunks indexed, 3 API endpoints, /knowledge-search page** |
| **Sprint 3** | **IKP Management UI + Re-indexing + KR Integration** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint 2** | **Engineering** | **742 tests, 6 API endpoints, /ikp-management page, chunk viewer, re-index trigger, KR batch creation** |
| **Sprint 4** | **AI QA Assistant + Reporting & Analytics** | **✅** | **2026-07-02** | **2026-07-02** | **Sprint 3** | **Engineering** | **808 tests, 13 API endpoints, /ai-assistant page, /analytics page, /reports page, CSV/Excel/PDF exports, 66 new tests** |
| **Sprint 5** | **Real LLM AI Provider Layer + Interactive Chat** | **✅** | **2026-07-03** | **2026-07-03** | **Sprint 4** | **Engineering** | **845 tests, 4 providers (OpenAI/Anthropic/Ollama/LOCAL_DEV), 7 agent modes, chat sessions, session sidebar, source panel, confidence scores, provider badge** |
| **RC1 Sprint** | **Release Candidate 1.0 — Final Feature Sprint** | **✅** | **2026-07-03** | **2026-07-03** | **Sprint 5** | **Engineering** | **884 tests, Qualification Intelligence MVP, AI provider verification, accessibility fix, sidebar icon fix, 5 deployment docs** |
| **Market-Ready Sprint** | **RC2 — Registration, ZIP Upload, Agent Router** | **✅** | **2026-07-03** | **2026-07-03** | **RC1 Sprint** | **Engineering** | **960 tests, public registration + email verification, admin approval workflow, bulk ZIP upload with ADIP classification, intelligent agent router (11 intents), /register + /verify-email pages** |
| **RC2 Completion Sprint** | **RC3 — Admin UI, ZIP UI, Agent Router Wired** | **✅** | **2026-07-04** | **2026-07-04** | **Market-Ready Sprint** | **Engineering** | **960 tests, /users admin page with approve/reject modals, /files/upload/zip bulk import UI, AI Assistant auto-mode detection, override toggle, suggested actions panel** |
| **RC4 Product Sprint** | **RC4 — AI Workspace, Multi-Agent, Landing Page, Workspaces** | **✅** | **2026-07-04** | **2026-07-04** | **RC2 Completion Sprint** | **Engineering** | **981 tests (+21), /ai-workspace full chat UI, multi-agent orchestration, /workspace institution overview, timeline, notification bell, commercial landing page at /, TSC clean, build clean** |
| **P2 Sprint 1** | **Commercial App Shell** | **✅** | **2026-07-05** | **2026-07-05** | **RC4** | **Engineering** | **CommandPalette (Ctrl+K), FloatingAIButton, Topbar redesign (institution badge/AI badge/user menu), Sidebar Brain icon fix, Dashboard greeting + quick actions, 6 reusable UI components** |
| **P2 Sprint 2** | **AI-First Executive Dashboard** | **✅** | **2026-07-05** | **2026-07-05** | **P2 Sprint 1** | **Engineering** | **9 dashboard sections, Framer Motion, Recharts (radial chart + sparklines), animated counters, timeline, service health, 981 tests, TSC clean, ESLint clean, build clean** |
| **P2 Sprint 3** | **Claude-Style AI Workspace** | **✅** | **2026-07-05** | **2026-07-05** | **P2 Sprint 2** | **Engineering** | **3-panel layout, agent thinking animation, NotebookLM source panel, slash commands, multi-agent cards, empty state, TSC clean** |
| **P3 Sprint 1** | **Production AI Provider Orchestration** | **✅** | **2026-07-06** | **2026-07-06** | **P2 Sprint 3** | **Engineering** | **1017 tests, ProviderManager cascade fallback, health endpoints (System Admin only), Gemini scaffold, AI Provider Settings page, Dashboard AI Health widget (SA only)** |
| **P3 Sprint 2** | **Real LLM Orchestrator + Streaming AI Responses** | **✅** | **2026-07-06** | **2026-07-06** | **P3 Sprint 1** | **Engineering** | **1051 tests (+34), LLM-assisted router, /ask-stream SSE endpoint, streaming workspace UI, simulated word-level chunking, non-stream fallback** |
| **P3 Sprint 3** | **Advanced RAG + Citation Verification** | **✅** | **2026-07-06** | **2026-07-06** | **P3 Sprint 2** | **Engineering** | **1091 tests (+40), source re-ranker, [SOURCE:N] context builder, citation verifier, grounding_status, metadata SSE event, grounding badge + citations UI** |
| **Split 1** | **SA University Foundation + UX Navigation Reorganisation** | **✅** | **2026-07-06** | **2026-07-06** | **P3 Sprint 3** | **Engineering** | **26 SA public university registry, institution provenance fields + migration, 7-item workspace sidebar, 5 workspace landing pages, executive dashboard, AI error UX with retry, 10 registry tests** |
| **Split 2 Wave 1** | **Institutional Knowledge Foundation** | **✅** | **2026-07-07** | **2026-07-07** | **Split 1** | **Engineering** | **11 new models (campuses/schools/qualifications/learning_outcomes/graduate_attributes/policies/policy_versions/institution_documents/accreditation_bodies/accreditations/contacts), Alembic migration b2c3d4e5f6a7, 15-file JSON data package (26 SA universities, provenance-tagged), idempotent seed pipeline, 6 tenant-isolated read-only API endpoints, /knowledge/foundation + /institution/profile pages, 11 new tests, TSC clean** |
| 6 | IKP Management + Full PDF Extraction | ⏳ | — | — | Sprint 1 | Engineering | |
| 7 | AI Knowledge Base Integration | ⏳ | — | — | 6 | Engineering | |
| 8 | Multi-Institution Production | ⏳ | — | — | 7 | Engineering | |

---

## Phase 5.4H Detail

### Phase 5.4H — ADIP Table Extraction & TUT ICT Completion

**Goal:** Add table extraction support and complete TUT ICT programme/module extraction to IKP v1.1.0.

**Start Date:** 2026-07-01  
**Completion Date:** 2026-07-01  
**Status:** ✅ Complete  
**Dependencies:** Phase 5.4G (ADIP Foundation)  
**Owner:** Engineering

#### Deliverable Checklist

| Deliverable | Status | File Path |
|-------------|--------|-----------|
| `table_extractor.py` — hybrid pdfplumber + tab-format engine | ✅ | `backend/app/adip/extractors/table_extractor.py` |
| `pdf_extractor.py` updated — tables populated in ExtractionResult | ✅ | `backend/app/adip/extractors/pdf_extractor.py` |
| `document_classifier.py` — `_INSTITUTION_OVERRIDES` Pass 1b | ✅ | `backend/app/adip/classifiers/document_classifier.py` |
| `tut_ict_mapper.py` — complete PDF-direct rewrite | ✅ | `backend/app/adip/mappers/tut_ict_mapper.py` |
| `run_tut_ict_extraction.py` — 8-file output + conflict detection | ✅ | `backend/app/adip/pipeline/run_tut_ict_extraction.py` |
| pdfplumber added to requirements.txt | ✅ | `backend/requirements.txt` |
| 18 new tests (5 new test classes) | ✅ | `backend/tests/test_adip.py` |
| IKP v1.1.0 extracted output (8 JSON files) | ✅ | `ikp/institutions/tut/2026/v1.1.0/extracted/` |
| AcademicPlanning misclassification fixed | ✅ | `_INSTITUTION_OVERRIDES` |
| CHANGELOG.md v0.5.8 | ✅ | `docs/00_Project/CHANGELOG.md` |
| PHASE_TRACKER.md updated | ✅ | This file |
| LESSONS_LEARNED.md LL-0013, LL-0014, LL-0015 | ✅ | `docs/00_Project/LESSONS_LEARNED.md` |
| ADIP_IMPLEMENTATION_ROADMAP.md updated | ✅ | `docs/09_AI/ADIP/ADIP_IMPLEMENTATION_ROADMAP.md` |
| TABLE_EXTRACTION_STRATEGY.md updated | ✅ | `docs/09_AI/ADIP/TABLE_EXTRACTION_STRATEGY.md` |
| AQAA_ENCYCLOPEDIA.md updated | ✅ | `docs/00_Project/AQAA_ENCYCLOPEDIA.md` |

#### Key Metrics

| Metric | Phase 5.4G | Phase 5.4H | Delta |
|--------|-----------|-----------|-------|
| Tables extracted | 0 | 107 | +107 |
| Programmes found | 8 | 22 | +14 |
| Modules found | 0 | 174 | +174 |
| Admission reqs | 0 | 16 | +16 |
| Mapping conflicts | 4 (early) | 0 | −4 |
| Backend tests | 472 | 490 | +18 |

---

## Phase 5.4E Detail

### Phase 5.4E — Product Foundation & Enterprise Knowledge Framework

**Goal:** Create the enterprise product foundation documents that govern all future AQAA development.

**Start Date:** 2026-06-29  
**Completion Date:** 2026-06-29  
**Status:** ✅ Complete  
**Dependencies:** Phase 5.4D (Documentation Standard)  
**Owner:** Engineering

#### Deliverable Checklist

| Deliverable | Status | File Path |
|-------------|--------|-----------|
| AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md | ✅ | `docs/00_Project/AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md` |
| AQAA_ENCYCLOPEDIA.md | ✅ | `docs/00_Project/AQAA_ENCYCLOPEDIA.md` |
| AQAA_GLOSSARY.md | ✅ | `docs/11_Reference/AQAA_GLOSSARY.md` |
| AQAA_DEVELOPER_PORTAL.md | ✅ | `docs/03_Developer_Guides/AQAA_DEVELOPER_PORTAL.md` |
| AQAA_PRODUCT_STRATEGY.md | ✅ | `docs/00_Project/AQAA_PRODUCT_STRATEGY.md` |
| CHANGELOG.md updated | ✅ | v0.5.5 entry added |
| PROJECT_DECISIONS.md updated | ✅ | DEC-0009, DEC-0010 added |
| PHASE_TRACKER.md updated | ✅ | This file |
| Cross-references added | ✅ | Encyclopedia links all docs |

---

## Phase 5.4D Detail

### Phase 5.4D — Engineering Documentation Standard

**Goal:** Create comprehensive documentation infrastructure for the AQAA project.

**Start Date:** 2026-06-29  
**Completion Date:** 2026-06-29  
**Status:** ✅ Complete  
**Dependencies:** Phase 5.4C (IKP Architecture)  
**Owner:** Engineering

#### Deliverable Checklist

| Deliverable | Status | File Path |
|-------------|--------|-----------|
| docs/ directory structure (14 dirs) | ✅ | `docs/` |
| AQAA_MASTER_ARCHITECTURE.md | ✅ | `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` |
| CLAUDE_DEVELOPMENT_STANDARD.md | ✅ | `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` |
| PROJECT_DECISIONS.md | ✅ | `docs/00_Project/PROJECT_DECISIONS.md` |
| CHANGELOG.md | ✅ | `docs/00_Project/CHANGELOG.md` |
| LESSONS_LEARNED.md | ✅ | `docs/00_Project/LESSONS_LEARNED.md` |
| AQAA_ROADMAP.md | ✅ | `docs/00_Project/AQAA_ROADMAP.md` |
| PHASE_TRACKER.md (this file) | ✅ | `docs/00_Project/PHASE_TRACKER.md` |
| ADR-0001 Standalone System | ⏳ | `docs/12_Decisions/ADR-0001-Standalone-System.md` |
| ADR-0002 Multi-Tenant Architecture | ⏳ | `docs/12_Decisions/ADR-0002-Multi-Tenant-Architecture.md` |
| ADR-0003 TUT Pilot | ⏳ | `docs/12_Decisions/ADR-0003-TUT-Pilot.md` |
| ADR-0004 IKP Architecture | ⏳ | `docs/12_Decisions/ADR-0004-Institutional-Knowledge-Package.md` |
| ADR-0005 AI-First Hybrid | ⏳ | `docs/12_Decisions/ADR-0005-AI-First-Hybrid-Architecture.md` |
| ADR-0006 Provenance and Versioning | ⏳ | `docs/12_Decisions/ADR-0006-Provenance-and-Versioning.md` |
| ADR-0007 Documentation-Driven Dev | ⏳ | `docs/12_Decisions/ADR-0007-Documentation-Driven-Development.md` |
| ADR-TEMPLATE.md | ⏳ | `docs/12_Decisions/ADR-TEMPLATE.md` |
| Subsystem documentation template | ⏳ | `docs/SUBSYSTEM_TEMPLATE/` |
| Section README files (13 sections) | ⏳ | `docs/01_Architecture/README.md` etc. |
| Root README.md update | ⏳ | `README.md` |

---

## Phase Completion Criteria

A phase is only marked ✅ Complete when ALL of the following are true:

| Criterion | Check |
|----------|-------|
| All deliverables in checklist are implemented | ✓ |
| `python -m pytest -q` passes (432+ tests) | ✓ |
| `npm run lint` exits 0 | ✓ |
| `npx tsc --noEmit` exits 0 | ✓ |
| `npm run build` exits 0 | ✓ |
| CHANGELOG.md updated | ✓ |
| PHASE_TRACKER.md updated | ✓ |
| Any new ADRs written | ✓ |
| Lessons Learned updated (if applicable) | ✓ |

---

## Template for Adding New Phases

When a new phase begins:

1. Add a row to the Phase Registry table
2. Create a Phase Detail section below
3. Define the deliverable checklist
4. Update CHANGELOG.md with the phase summary when complete
5. Update AQAA_ROADMAP.md
6. Update completion date when done
