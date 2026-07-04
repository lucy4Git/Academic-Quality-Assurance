# AQAA — Master Encyclopedia

**Document ID:** ENC-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29  
**Purpose:** Master index and navigation guide for the entire AQAA platform

> This document is the map of AQAA. Everything in the platform is referenced here.  
> If it exists in AQAA, it has an entry in this encyclopedia.

---

## Platform Overview

AQAA (Academic Quality Assurance Agent) is an enterprise, AI-augmented, multi-tenant academic quality assurance platform for South African higher education institutions. It digitises and automates the module folder audit cycle, maintains institutional knowledge packages (IKP), and governs all QA evidence through a structured workflow.

**Current version:** 0.6.0  
**Tech stack:** Next.js 14 + FastAPI + PostgreSQL + Redis + Qdrant  
**Pilot institution:** Tshwane University of Technology (TUT) — Faculty of ICT  
**Backend tests:** 532 passing

---

## Documentation Map

### Master Documents (`docs/00_Project/`)

| Document | Purpose | Read When |
|----------|---------|-----------|
| [`AQAA_MASTER_ARCHITECTURE.md`](00_Project/AQAA_MASTER_ARCHITECTURE.md) | Single source of truth for all architecture | Before any structural change |
| [`CLAUDE_DEVELOPMENT_STANDARD.md`](00_Project/CLAUDE_DEVELOPMENT_STANDARD.md) | Engineering constitution | Start of every session |
| [`AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md`](00_Project/AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md) | Full product requirements | Product planning, scope decisions |
| [`AQAA_PRODUCT_STRATEGY.md`](00_Project/AQAA_PRODUCT_STRATEGY.md) | Commercial strategy and market positioning | Commercial decisions |
| [`PROJECT_DECISIONS.md`](00_Project/PROJECT_DECISIONS.md) | All project-level decisions (DEC-0001+) | Before making strategic changes |
| [`CHANGELOG.md`](00_Project/CHANGELOG.md) | Full version history | Tracking changes |
| [`LESSONS_LEARNED.md`](00_Project/LESSONS_LEARNED.md) | Problems, causes, and solutions | Debugging, avoiding past mistakes |
| [`AQAA_ROADMAP.md`](00_Project/AQAA_ROADMAP.md) | Phase map and commercial roadmap | Planning future work |
| [`PHASE_TRACKER.md`](00_Project/PHASE_TRACKER.md) | Phase status with deliverable checklists | Tracking phase progress |
| [`AQAA_ENCYCLOPEDIA.md`](00_Project/AQAA_ENCYCLOPEDIA.md) | This document — master index | Navigation |

### Architecture (`docs/01_Architecture/`)

| Document | Status |
|----------|--------|
| `DATA_MODEL.md` | ⏳ Planned |
| `API_DESIGN.md` | ⏳ Planned |
| `SECURITY_MODEL.md` | ⏳ Planned |
| `FRONTEND_ARCHITECTURE.md` | ⏳ Planned |
| `BACKEND_ARCHITECTURE.md` | ⏳ Planned |
| `STORAGE_ARCHITECTURE.md` | ⏳ Planned |
| `AUDIT_ENGINE_ARCHITECTURE.md` | ⏳ Planned |
| `WORKFLOW_ARCHITECTURE.md` | ⏳ Planned |
| `KNOWLEDGE_REVIEW_CENTRE_ARCHITECTURE.md` | ✅ Complete |

### Implementation (`docs/02_Implementation/`)

| Document | Status |
|----------|--------|
| `PHASE1_FOUNDATION.md` | ⏳ Planned |
| `INSTITUTION_HIERARCHY.md` | ⏳ Planned |
| `KNOWLEDGE_REVIEW_CENTRE_IMPLEMENTATION_GUIDE.md` | ✅ Complete |
| `AUDIT_ENGINE.md` | ⏳ Planned |
| `EVIDENCE_SYSTEM.md` | ⏳ Planned |
| `WORKFLOW_ENGINE.md` | ⏳ Planned |
| `IKP_PIPELINE.md` | ⏳ Planned (Phase 5.4E) |

### Developer Guides (`docs/03_Developer_Guides/`)

| Document | Status |
|----------|--------|
| [`AQAA_DEVELOPER_PORTAL.md`](03_Developer_Guides/AQAA_DEVELOPER_PORTAL.md) | ✅ Active |
| `ENVIRONMENT_SETUP.md` | ⏳ Planned |
| `BACKEND_PATTERNS.md` | ⏳ Planned |
| `FRONTEND_PATTERNS.md` | ⏳ Planned |
| `DATABASE_GUIDE.md` | ⏳ Planned |

### User Guides (`docs/04_User_Guides/`)

| Document | Status |
|----------|--------|
| `GETTING_STARTED.md` | ⏳ Planned |
| `QA_OFFICER_GUIDE.md` | ⏳ Planned |
| `COORDINATOR_GUIDE.md` | ⏳ Planned |

### Testing (`docs/05_Testing/`)

| Document | Status |
|----------|--------|
| `TEST_STRATEGY.md` | ⏳ Planned |
| `BACKEND_TESTING.md` | ⏳ Planned |
| `TENANT_ISOLATION_TESTS.md` | ⏳ Planned |

### Deployment (`docs/07_Deployment/`)

| Document | Status |
|----------|--------|
| `LOCAL_DEPLOYMENT.md` | ⏳ Planned |
| `PRODUCTION_DEPLOYMENT.md` | ⏳ Planned (Phase 8) |

### API Reference (`docs/08_API/`)

| Document | Status |
|----------|--------|
| `AUTH_API.md` | ⏳ Planned |
| `INSTITUTION_HIERARCHY_API.md` | ⏳ Planned |
| `AUDIT_ENGINE_API.md` | ⏳ Planned |
| `EVIDENCE_API.md` | ⏳ Planned |
| `WORKFLOW_API.md` | ⏳ Planned |
| `AI_AGENTS_API.md` | ⏳ Planned |

### AI Documentation (`docs/09_AI/`)

| Document | Status |
|----------|--------|
| `AGENT_ARCHITECTURE.md` | ⏳ Planned |
| `AI_RULES_FORMAT.md` | ⏳ Planned |
| `CONFIDENCE_SCORING.md` | ⏳ Planned |
| `IKP_AI_INTEGRATION.md` | ⏳ Planned (Phase 7) |

### ADIP — Academic Document Intelligence Platform (`docs/09_AI/ADIP/`)

| Document | Status | Description |
|----------|--------|-------------|
| `ADIP_MASTER_ARCHITECTURE.md` | ✅ Active | 10-layer architecture, 30+ formats, confidence model |
| `DOCUMENT_SOURCE_LAYER.md` | ✅ Active | 6 source types, registry, hash, immutable storage |
| `DOCUMENT_CLASSIFICATION_ENGINE.md` | ✅ Active | 3-pass classification, 20+ document types |
| `DOCUMENT_EXTRACTION_ENGINE.md` | ✅ Active | All format extractors, DocumentChunk model |
| `DOCUMENT_VALIDATION_ENGINE.md` | ✅ Active | 6-stage validation, confidence formula and gates |
| `KNOWLEDGE_MAPPING_ENGINE.md` | ✅ Active | Extracted text → IKP entity candidates |
| `PROVENANCE_ENGINE.md` | ✅ Active | Per-field ProvenanceAnchor with exact source location |
| `KNOWLEDGE_INDEXING_ENGINE.md` | ✅ Active | PostgreSQL + FTS + Qdrant + knowledge graph |
| `AI_READINESS_ENGINE.md` | ✅ Active | RAG chunks, confidence reasoning, contradiction detection |
| `OCR_AND_MULTIMODAL_STRATEGY.md` | ✅ Active | EasyOCR, scanned PDF, image OCR |
| `TABLE_EXTRACTION_STRATEGY.md` | ✅ Active | pdfplumber + tab-format (TUT); real findings from Phase 5.4H |
| `VIDEO_AUDIO_EXTRACTION_STRATEGY.md` | ✅ Active | Whisper + ffmpeg (Phase 7 implementation) |
| `SECURITY_AND_GOVERNANCE.md` | ✅ Active | Tenant isolation, RBAC, immutability, POPIA |
| `TUT_PILOT_ADIP_PLAN.md` | ✅ Active | TUT pilot plan: documents, expected output, validation |
| `ADIP_IMPLEMENTATION_ROADMAP.md` | ✅ Active | Phase 5.4G through Phase 8 tasks and library list |

### Knowledge Base (`docs/10_Knowledge_Base/`)

| Document | Status |
|----------|--------|
| `IKP_ARCHITECTURE.md` | ⏳ Planned (extract from Phase 5.4C session) |
| `IKP_JSON_SCHEMA.md` | ⏳ Planned |
| `TUT_PILOT_IKP.md` | ⏳ Planned |

### Reference (`docs/11_Reference/`)

| Document | Status |
|----------|--------|
| [`AQAA_GLOSSARY.md`](11_Reference/AQAA_GLOSSARY.md) | ✅ Active |
| `NQF_REFERENCE.md` | ⏳ Planned |
| `RBAC_MATRIX.md` | ⏳ Planned |
| `ENUM_VALUES.md` | ⏳ Planned |
| `CHECKLIST_ITEMS.md` | ⏳ Planned |
| `WORKFLOW_STATES.md` | ⏳ Planned |

### Architecture Decision Records (`docs/12_Decisions/`)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](12_Decisions/ADR-0001-Standalone-System.md) | Standalone System | ✅ Accepted |
| [ADR-0002](12_Decisions/ADR-0002-Multi-Tenant-Architecture.md) | Multi-Tenant Architecture | ✅ Accepted |
| [ADR-0003](12_Decisions/ADR-0003-TUT-Pilot.md) | TUT Pilot Institution | ✅ Accepted |
| [ADR-0004](12_Decisions/ADR-0004-Institutional-Knowledge-Package.md) | Institutional Knowledge Package | ✅ Accepted |
| [ADR-0005](12_Decisions/ADR-0005-AI-First-Hybrid-Architecture.md) | AI-First Hybrid Architecture | ✅ Accepted |
| [ADR-0006](12_Decisions/ADR-0006-Provenance-and-Versioning.md) | Provenance and Versioning | ✅ Accepted |
| [ADR-0007](12_Decisions/ADR-0007-Documentation-Driven-Development.md) | Documentation-Driven Development | ✅ Accepted |

### Research (`docs/13_Research/`)

| Document | Date | Description |
|----------|------|-------------|
| `TUT_5.4A_PROVENANCE_AUDIT.md` | 2026-06-29 | Database provenance audit — all records traced |
| `TUT_5.4B_KNOWLEDGE_COLLECTION.md` | 2026-06-29 | Official TUT data collection |
| `TUT_5.4C_SOURCE_REVIEW.md` | 2026-06-29 | Source classification, ICT pilot dataset |

---

## Architecture Map

```
AQAA Platform
│
├── Frontend (Next.js 14)
│   ├── Authentication — /login, /api/auth/
│   ├── Institution Hierarchy — /institutions, /faculties, /departments, /programmes, /modules
│   ├── Audit Engine — /audits, /audits/[id]
│   ├── Evidence — /files, /files/upload
│   ├── Workflow — /workflow, /workflow/[id]
│   ├── Notifications — /notifications
│   ├── Calendar — /calendar
│   ├── Approvals — /approvals
│   └── Dashboard — /dashboard
│
├── API Proxy (Next.js API Routes)
│   └── /api/proxy/[...path] — reads httpOnly cookie, injects Bearer header
│
├── Backend (FastAPI)
│   ├── Authentication — /api/v1/auth/*
│   ├── Institution Hierarchy — /api/v1/institutions, /faculties, /departments, /programmes, /modules
│   ├── Manual Audit Engine — /api/v1/module-audits, /audits
│   ├── Evidence — /api/v1/evidence, /files
│   ├── AI Agents — /api/v1/audits (trigger), /assessment-audits, etc.
│   ├── Audit History — /api/v1/audits/{id}/history
│   ├── Workflow — /api/v1/workflow
│   ├── Comments — /api/v1/comments
│   ├── Notifications — /api/v1/notifications
│   ├── Approvals — /api/v1/approvals
│   └── Dashboard — /api/v1/dashboard
│
├── Data Layer
│   ├── PostgreSQL — primary store (all entities)
│   ├── Redis — cache
│   └── Qdrant — vector embeddings (AI agents)
│
├── Institutional Knowledge
│   └── IKP packages — ikp/institutions/{code}/{year}/v{version}/
│
└── Demo/Seed Data
    └── database/seed_data/ — GFU + RCT demo institutions
```

---

## API Map

All API routes are prefixed with `/api/v1/`.

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/token` | None | OAuth2 form login (Swagger) |
| POST | `/auth/login` | None | JSON login |
| POST | `/auth/refresh` | Cookie | Refresh access token |
| GET | `/auth/me` | Bearer | Current user profile |

### Institution Hierarchy

| Method | Path | Min Role | Description |
|--------|------|----------|-------------|
| GET/POST | `/institutions` | QAO | List/create institutions |
| GET/PUT/DELETE | `/institutions/{id}` | QAO | Get/update/delete institution |
| GET/POST | `/faculties` | Dean | List/create faculties |
| GET/POST | `/departments` | HOD | List/create departments |
| GET/POST | `/programmes` | All | List/create programmes |
| GET/POST | `/modules` | All | List/create modules |

### Manual Audit Engine

| Method | Path | Min Role | Description |
|--------|------|----------|-------------|
| GET/POST | `/module-audits` | Coordinator | List/create audits |
| GET | `/module-audits/{id}` | Any | Get audit detail |
| PATCH | `/module-audits/{id}` | Coordinator | Update checklist |
| DELETE | `/module-audits/{id}` | QAO | Delete audit |
| GET | `/audits/{id}/history` | Any | Audit timeline |

### Evidence

| Method | Path | Description |
|--------|------|-------------|
| POST | `/evidence/upload` | Upload file as evidence |
| GET | `/evidence/{id}/download` | Download file |
| GET | `/evidence/{id}/preview` | Inline preview |
| DELETE | `/evidence/{id}` | Delete evidence |
| GET | `/audits/{audit_id}/evidence` | All evidence for audit |

### Workflow

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workflow/assign` | Assign audit to user |
| POST | `/workflow/status` | Change workflow status |
| GET | `/workflow` | List all workflow items |
| GET | `/workflow/{audit_id}` | Get single workflow |
| POST | `/approvals/approve` | Approve audit |
| POST | `/approvals/reject` | Reject audit |
| POST | `/approvals/return` | Return for corrections |
| POST | `/approvals/request-evidence` | Request evidence collection |

### Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | List notifications |
| PATCH | `/notifications/{id}/read` | Mark one as read |
| PATCH | `/notifications/read-all` | Mark all as read |

### AI Agents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audits/modules/{id}/trigger` | Trigger Module Folder Audit |
| POST | `/assessment-audits/modules/{id}/trigger` | Trigger Assessment Compliance |
| POST | `/moderation-audits/modules/{id}/trigger` | Trigger Moderation Compliance |
| POST | `/attendance-audits/modules/{id}/trigger` | Trigger Attendance Compliance |
| POST | `/evidence-audits/modules/{id}/trigger` | Trigger Evidence Verification |
| POST | `/outcome-alignment-audits/modules/{id}/trigger` | Trigger Outcome Alignment |
| POST | `/accreditation-readiness-audits/modules/{id}/trigger` | Trigger Accreditation Readiness |
| POST | `/programme-review-audits/programmes/{id}/trigger` | Trigger Programme Review |
| GET | `/audits/{run_id}` | Poll for AI run status |
| GET | `/audits/{run_id}/report` | Get completed report |

---

## AI Map

### Agent Portfolio

| Agent | File | Scope | Trigger Prefix |
|-------|------|-------|---------------|
| Module Folder Audit | `backend/app/agents/module_folder_audit.py` | Module | `/audits` |
| Assessment Compliance | `backend/app/agents/assessment_compliance.py` | Module | `/assessment-audits` |
| Moderation Compliance | `backend/app/agents/moderation_compliance.py` | Module | `/moderation-audits` |
| Attendance Compliance | `backend/app/agents/attendance_compliance.py` | Module | `/attendance-audits` |
| Evidence Verification | `backend/app/agents/evidence_verification.py` | Module | `/evidence-audits` |
| Outcome Alignment | `backend/app/agents/outcome_alignment.py` | Module | `/outcome-alignment-audits` |
| Accreditation Readiness | `backend/app/agents/accreditation_readiness.py` | Module | `/accreditation-readiness-audits` |
| Programme Review | `backend/app/agents/programme_review_agent.py` | Programme | `/programme-review-audits` |

### AI Support Systems

| System | Files | Purpose |
|--------|-------|---------|
| Document parsing | `backend/app/parsers/` | PDF, DOCX, XLSX, image OCR |
| Classification | `backend/app/services/classification_service.py` | Document type classification |
| Extraction | `backend/app/services/extraction_service.py` | Text extraction from documents |
| Scoring common | `backend/app/agents/scoring_common.py` | Shared compliance scoring logic |

---

## Knowledge Base Map

### IKP Status

| Institution | Code | IKP Version | Status | Scope |
|-------------|------|-------------|--------|-------|
| Greenfield University (demo) | GFU | N/A | Seed data only | Full hierarchy |
| Riverside College of Technology (demo) | RCT | N/A | Seed data only | Full hierarchy |
| Tshwane University of Technology | TUT | v1.1.0 | ✅ Extracted (Phase 5.4H) | ICT Faculty — 22 programmes, 174 modules, 16 admission reqs |

### IKP File Locations

```
ikp/
└── institutions/
    └── tut/
        └── 2026/
            ├── v1.0.0/          ← Sealed (HTML-verified only)
                ├── package.json
                ├── institution.json
                ├── campuses/
                │   ├── soshanguve-south.json
                │   ├── emahleni.json
                │   └── polokwane.json
                ├── faculties/
                │   └── ict/
                │       ├── faculty.json
                │       └── departments/
                │           ├── computer-science/
                │           ├── computer-systems-engineering/
                │           ├── informatics/
                │           └── information-technology/
                └── provenance/
            └── v1.1.0/          ← Active (ADIP extracted — Phase 5.4H)
                └── extracted/
                    ├── documents.json
                    ├── chunks.json
                    ├── tables.json
                    ├── programme_candidates.json
                    ├── module_candidates.json
                    ├── admission_candidates.json
                    ├── mapping_conflicts.json
                    └── extraction_summary.json
```

### Data Sources by Confidence Level

| Confidence | Source Type | Example |
|------------|------------|---------|
| 0.95–1.00 | Official HTML (official tut.ac.za pages) | Dept names, NQF levels, contacts |
| 0.85–0.94 | Official PDF extracted | APS, credits, modules (pending) |
| 0.70–0.84 | HEQSF national standard | Credit minimums |
| 0.45 | Secondary website | briefly.co.za APS claims — DO NOT LOAD |

---

## Database Map

### Core Tables

| Table | Model File | Purpose |
|-------|-----------|---------|
| `institutions` | `backend/app/models/institution.py` | Tenant root |
| `faculties` | `backend/app/models/faculty.py` | Faculty (note: explicit `__tablename__`) |
| `departments` | `backend/app/models/department.py` | Department |
| `programmes` | `backend/app/models/programme.py` | Academic programme |
| `modules` | `backend/app/models/module.py` | Taught module |
| `users` | `backend/app/models/user.py` | Platform users |

### Audit Tables

| Table | Model File | Purpose |
|-------|-----------|---------|
| `module_audits` | `backend/app/models/module_audit.py` | Manual QA audit |
| `audit_checklist_items` | `backend/app/models/module_audit.py` | 10 checklist items per audit |
| `audit_evidence` | `backend/app/models/audit_evidence.py` | Uploaded evidence files |
| `audit_history` | `backend/app/models/audit_history.py` | Immutable event timeline |
| `audit_comments` | `backend/app/models/audit_comment.py` | Comment threads |

### AI Tables

| Table | Model File | Purpose |
|-------|-----------|---------|
| `audit_runs` | `backend/app/models/audit_run.py` | AI agent run records |
| `audit_findings` | `backend/app/models/audit_finding.py` | AI-generated findings |

### Workflow / Notifications

| Table | Model File | Purpose |
|-------|-----------|---------|
| `module_audits.workflow_status` | Column on `module_audits` | 9-state workflow |
| `notifications` | `backend/app/models/notification.py` | In-app notifications |

### Applied Migrations (in order)

| Revision ID | Description |
|------------|-------------|
| `99c7b97c9a76` | Initial schema |
| `bcb42a8b6462` | Add programme QA fields |
| `6bcc7db53782` | Add module audit tables |
| `a1afe7223e2a` | Add audit evidence table |
| `146ff3d10cd9` | Add audit history table |
| `2a7b17360d01` | Phase 5 workflow, comments, notifications |

---

## Subsystem Template Map

When building a new subsystem, use these templates:

| Template | Path | Use For |
|----------|------|---------|
| Architecture | `docs/SUBSYSTEM_TEMPLATE/ARCHITECTURE.md` | New subsystem design |
| Implementation Guide | `docs/SUBSYSTEM_TEMPLATE/IMPLEMENTATION_GUIDE.md` | Build instructions |
| User Guide | `docs/SUBSYSTEM_TEMPLATE/USER_GUIDE.md` | End-user docs |
| Testing Guide | `docs/SUBSYSTEM_TEMPLATE/TESTING_GUIDE.md` | Test plans |
| Maintenance Guide | `docs/SUBSYSTEM_TEMPLATE/MAINTENANCE_GUIDE.md` | Operations |
| ADR | `docs/12_Decisions/ADR-TEMPLATE.md` | Architecture decisions |

---

*Update this encyclopedia whenever a new document is created or a new subsystem is implemented.*
