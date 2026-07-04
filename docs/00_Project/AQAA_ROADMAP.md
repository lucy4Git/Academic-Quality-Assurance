# AQAA — Product Roadmap

**Document ID:** ROAD-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

---

## Current Status

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Frontend Foundation | ✅ Complete |
| Phase 2C | Institution Hierarchy CRUD | ✅ Complete |
| Phase 3A | RBAC System | ✅ Complete |
| Phase 3B | Programme QA Fields + Dashboard | ✅ Complete |
| Phase 3C | Module Management | ✅ Complete |
| Phase 3D | Academic Structure Verification | ✅ Complete |
| Phase 4A | Manual QA Audit Engine | ✅ Complete |
| Phase 4B | Evidence Upload + File Library | ✅ Complete |
| Phase 4C | Evidence Preview + Audit History | ✅ Complete |
| Phase 5 | Workflow Automation + Notifications | ✅ Complete |
| Phase 5.4A | Database Provenance Audit | ✅ Complete |
| Phase 5.4B | TUT Academic Knowledge Collection | ✅ Complete |
| Phase 5.4C | IKP Architecture Design | ✅ Complete |
| **Phase 5.4D** | **Engineering Documentation Standard** | **🔄 In Progress** |
| Phase 5.4E | TUT ICT Pilot Database Load | ⏳ Planned |
| Phase 6 | IKP Management + PDF Extraction | ⏳ Planned |
| Phase 7 | AI Knowledge Base Integration | ⏳ Future |
| Phase 8 | Multi-Institution Production | ⏳ Future |

---

## Completed Phases

### Phase 1 — Frontend Foundation ✅
**Delivered:** Next.js 14 App Router, authentication (httpOnly JWT cookies), AppShell, sidebar with RBAC-aware navigation, TanStack Query, Zustand, route protection middleware.

### Phase 2C — Institution Hierarchy CRUD ✅
**Delivered:** Full CRUD for Institution, Faculty, Department, Programme. Multi-level hierarchy enforced. RBAC on all management operations.

### Phase 3A — Complete RBAC System ✅
**Delivered:** 7-role hierarchy (SA → Student). Frontend middleware, `RoleGuard` component, `useRole` hook. `/forbidden` page.

### Phase 3B — Programme QA Fields + Dashboard ✅
**Delivered:** Extended Programme model (NQF level, credits, status). Dashboard entity counts per institution/platform.

### Phase 3C — Module Management ✅
**Delivered:** Module CRUD (code, name, credits, semester, academic year, lecturer). Complete Institution → Faculty → Department → Programme → Module hierarchy.

### Phase 3D — Academic Structure Verification ✅
**Delivered:** End-to-end test of full hierarchy. Confirmed all FK relationships functional.

### Phase 4A — Manual QA Audit Engine ✅
**Delivered:** `ModuleAudit` + `AuditChecklistItem` models. 10-item QA checklist. Compliance percentage calculation. Audit Centre, Create Audit, Audit Detail pages. DRAFT → COMPLIANT/AT_RISK/NON_COMPLIANT status machine.

### Phase 4B — Evidence Upload + File Library ✅
**Delivered:** `AuditEvidence` model. Multipart file upload. Evidence linked to checklist items. File Library page. Upload Evidence page with drag-and-drop.

### Phase 4C — Evidence Preview + Audit History ✅
**Delivered:** `AuditHistory` model (immutable timeline). Evidence inline preview (PDF/image/text). `GET /audits/{id}/history` endpoint. Timeline component in Audit Detail page.

### Phase 5 — Workflow Automation + Notifications ✅
**Delivered:** 9-state workflow (Draft → Archived). Audit assignment with priority and due date. Comment threads with edit/resolve/delete. Notification centre (10 types). Approval system (approve/reject/return/request-evidence). Email templates. Dashboard workflow widget. Audit Calendar.

### Phase 5.4A — Database Provenance Audit ✅
**Delivered:** Full audit of all database records. Seed script inventory. Record count reconciliation. FK relationship verification. Dashboard data source trace. Recommendations.

### Phase 5.4B — TUT Academic Knowledge Collection ✅
**Delivered:** Official TUT data collection (institution, campuses, 8 faculties, 35 departments, 200+ programmes). Source classification (official vs secondary). ICT faculty detailed verification from official tut.ac.za department pages.

### Phase 5.4C — IKP Architecture Design ✅
**Delivered:** Complete IKP specification (8 layers). JSON schema. Folder structure. ERD. Knowledge Graph. Provenance model. Versioning model. 9-stage ingestion pipeline. AI knowledge flow. TUT ICT Pilot IKP v1.0.0 (34 verified records). Multi-institution strategy. Implementation roadmap.

---

## Current Phase

### Phase 5.4G — ADIP MVP: TUT PDF Extraction ⏳
**Goal:** Implement minimum viable ADIP (Layers 1–7) to extract TUT ICT Prospectus and populate IKP v1.1.0.  
**Prerequisites:** Phase 5.4F (ADIP Architecture — complete)  
**Key libraries:** `pdfminer.six`, `camelot-py[cv]`, `pymupdf`, `easyocr`  
**Expected output:** IKP v1.1.0 with 25 programmes + APS + credits + ~75 modules + academic rules  
**Next step:** Phase 5.4H — write `seed_tut.py` and load IKP v1.1.0 into AQAA

---

## Completed Phases

### Phase 5.4F — ADIP Architecture ✅
**Delivered:** 15 architecture documents in `docs/09_AI/ADIP/`, ADR-0008. Full format-agnostic, provenance-aware, 10-layer ADIP design. TUT pilot plan. Implementation roadmap.

### Phase 5.4E — Product Foundation ✅
**Delivered:** PRD, Encyclopedia, Glossary, Developer Portal, Product Strategy. 5 documents, 3 existing docs updated.

### Phase 5.4D — Engineering Documentation Standard ✅
**Goal:** Transform AQAA into a documentation-driven enterprise project.  
**Deliverables:**
- `docs/` 14-directory structure ✅
- `AQAA_MASTER_ARCHITECTURE.md` ✅
- `CLAUDE_DEVELOPMENT_STANDARD.md` ✅
- `PROJECT_DECISIONS.md` ✅
- `CHANGELOG.md` ✅
- `LESSONS_LEARNED.md` ✅
- `AQAA_ROADMAP.md` ✅ (this file)
- `PHASE_TRACKER.md` ⏳
- ADR-0001 through ADR-0007 ⏳
- Subsystem templates ⏳
- Updated README.md ⏳

---

## Planned Phases

### Phase 5.4E — TUT ICT Pilot Database Load
**Goal:** Load the verified TUT ICT pilot dataset into AQAA as a third tenant.  
**Prerequisites:** Phase 5.4C (IKP Architecture), Phase 5.4D (Documentation), PDF extraction.  
**Key tasks:**
- Install `pdfminer.six` in backend environment
- Extract `Part6_ICT_Prospectus.pdf` (1.3 MB — already downloaded)
- Validate extracted data against IKP confidence thresholds
- Write `database/seed_data/seed_tut.py`
- Load 1 institution + 3 campuses + 1 faculty + 4 departments + 25 programmes + modules
- Validate GFU/RCT data unchanged

---

### Phase 6 — IKP Management + Full PDF Extraction
**Goal:** Build IKP management into the AQAA platform itself.  
**Key tasks:**
- IKP management UI (view, compare, validate packages)
- Human review queue for low-confidence fields
- Extract all 8 TUT faculty prospectus PDFs
- Load remaining TUT faculties (7 remaining)
- Knowledge gap tracking in AQAA database
- Academic calendar integration
- Examination rules policy ingestion

---

### Phase 7 — AI Knowledge Base Integration
**Goal:** Connect the IKP to AQAA's AI agents for institution-aware auditing.  
**Key tasks:**
- Load IKP AI rules into audit agent pipeline
- IKP-aware audit templates (agents use institution-specific rules)
- Confidence-weighted findings (AI cites its data source and confidence)
- Natural language QA queries
- Predictive gap detection before audit run
- Qdrant vector embeddings for policy text

---

### Phase 8 — Multi-Institution Production Deployment
**Goal:** Deploy AQAA for use by multiple institutions simultaneously.  
**Key tasks:**
- Second institution onboarding (University of Pretoria or DUT — TBD)
- Production deployment configuration
- Backup and disaster recovery
- Performance testing (multi-tenant query optimisation)
- Audit logging and compliance reporting
- User onboarding flows

---

## Future Commercial Roadmap

| Stage | Description | Target |
|-------|-------------|--------|
| **Pilot** | TUT ICT Faculty controlled pilot | 2026 Q3 |
| **Institution** | Full TUT deployment (all 8 faculties) | 2026 Q4 |
| **Consortium** | 3–5 South African institutions | 2027 |
| **National** | All 26 South African public universities | 2028 |
| **TVET** | TVET colleges and community colleges | 2028–2029 |
| **Continental** | Pan-African higher education | 2029+ |
| **International** | International institutions (with NQF mapping) | 2030+ |

---

## Backlog (Unscheduled)

| Item | Priority | Notes |
|------|----------|-------|
| SMTP email delivery | Medium | Templates exist; delivery service not configured |
| SAQA NQF API integration | Low | Would auto-verify NQF levels from official SAQA API |
| ECSA registration lookup | Low | Verify engineering programme professional body status |
| Mobile-responsive audit forms | Medium | Current UI desktop-first |
| Offline evidence upload | Low | For campuses with poor connectivity |
| CHE accreditation integration | Future | Direct link to CHE programme database |
| Student portal (read-only) | Future | Students view their own programme audit status |
| External moderation workflow | Future | Invite external moderators to review audit findings |
| Bulk audit triggers | Future | Trigger all modules in a faculty simultaneously |
| Academic year rollover | Future | Auto-create new audit cycle at year change |
