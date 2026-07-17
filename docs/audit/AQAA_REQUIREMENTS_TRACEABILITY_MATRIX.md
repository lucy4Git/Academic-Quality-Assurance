# AQAA Requirements Traceability Matrix

**Audit Date:** 2026-07-13  
**Purpose:** Map stated system requirements to implementation evidence  
**Evidence Source:** CLAUDE.md, CHANGELOG, PHASE_TRACKER, direct testing

---

## Core Platform Requirements

| Requirement | Source | Implementation | Evidence | Status |
|-------------|--------|---------------|----------|--------|
| Multi-tenancy — institution isolation | CLAUDE.md | `institution_id` scoping in all service queries | Live: QA officer sees 1 institution; Admin sees 28 | ✅ VERIFIED |
| 7-tier RBAC hierarchy | CLAUDE.md | `UserRole` enum; role guards in `dependencies.py` | Live: RBAC enforced on API + frontend routes | ✅ VERIFIED |
| JWT HS256 authentication | CLAUDE.md | `auth_service.py`; httpOnly cookies via Next.js proxy | Live: login returns tokens; cookies set correctly | ✅ VERIFIED |
| 5-level institutional hierarchy | CLAUDE.md | Institution → Faculty → Dept → Programme → Module models | Live: all levels navigable via API | ✅ VERIFIED |
| PostgreSQL primary store | CLAUDE.md | SQLAlchemy 2 async + asyncpg | Live: DB queries return real data | ✅ VERIFIED |
| Redis cache | CLAUDE.md | Container running | Redis usage not confirmed in code audit | ⚠️ PARTIAL |
| Qdrant vector store | CLAUDE.md | Qdrant container + indexing | Running; populated with hash embeddings (not semantic) | ⚠️ BROKEN |
| MongoDB document store | CLAUDE.md | "architected, not yet wired" | No container, no connection code | ❌ NOT STARTED |

---

## AI Audit Agent Requirements

| Agent | Required By | Trigger Path | Report Service | Status |
|-------|-------------|-------------|----------------|--------|
| Module Folder Audit | Phase 2 | `/audits/modules/{id}/trigger` | — | ✅ LIVE-TESTED |
| Assessment Compliance | Phase 2 | `/assessment-audits/modules/{id}/trigger` | `assessment_report_service.py` | ✅ CODE COMPLETE |
| Moderation Compliance | Phase 2 | `/moderation-audits/modules/{id}/trigger` | `moderation_report_service.py` | ✅ CODE COMPLETE |
| Attendance Compliance | Phase 2 | `/attendance-audits/modules/{id}/trigger` | `attendance_report_service.py` | ✅ CODE COMPLETE |
| Evidence Verification | Phase 2 | `/evidence-audits/modules/{id}/trigger` | `evidence_report_service.py` | ✅ CODE COMPLETE |
| Outcome Alignment | Phase 2 | `/outcome-alignment-audits/modules/{id}/trigger` | `outcome_alignment_report_service.py` | ✅ CODE COMPLETE |
| Accreditation Readiness | Phase 2 | `/accreditation-readiness-audits/modules/{id}/trigger` | `accreditation_readiness_report_service.py` | ✅ CODE COMPLETE |
| Programme Review | Phase 2 | `/programme-review-audits/programmes/{id}/trigger` | `programme_review_report_service.py` | ✅ CODE COMPLETE |

---

## Frontend Page Requirements

| Page | Required Role(s) | Frontend Status | Backend Status |
|------|-----------------|-----------------|----------------|
| Home / Dashboard | All | ✅ Role-specific, live-tested | N/A |
| AI Workspace | All | ✅ 3-panel, live-tested | ✅ Streaming AI ask |
| Workspace Landing | Lecturer+ | ✅ Role-specific prompts | N/A |
| Knowledge Landing | Lecturer+ | ✅ 6 cards | N/A |
| Quality Landing | Coordinator+ | ✅ 8 cards | N/A |
| Administration Landing | Admin | ✅ 9 cards | N/A |
| Audit Centre | Coordinator+ | ✅ AuditCentre.tsx (~9KB) | ⚠️ Global list broken |
| Findings | QA+ | ❌ PlaceholderPage | ❌ No list route |
| Workflow | Coordinator+ | ✅ WorkflowListView (~6KB) | ✅ route exists |
| Approvals | QA+ | ✅ ApprovalsView (~8KB) | ✅ route exists |
| Reports | QA+ | ✅ ReportsView (~4KB) | ✅ route exists (PDF text-only) |
| Analytics | Lecturer+ | ✅ AnalyticsView (~7KB) | ✅ route exists |
| Accreditation | QA+ | ❌ PlaceholderPage | ✅ Agent + route complete |
| Knowledge Extraction | QA+ | ✅ ExtractionView | ✅ route exists |
| Knowledge Acquisition | QA+ | ✅ AcquisitionView | ✅ route exists |
| Knowledge Review | QA+ | ✅ ReviewView | ✅ route exists |
| Compliance Reports | QA+ | ❌ PlaceholderPage | ✅ `/reporting/compliance-summary` |
| Settings / Profile | All | ❌ PlaceholderPage | ❓ Endpoint not confirmed |
| Settings / Security | All | ❌ PlaceholderPage | ❓ Endpoint not confirmed |
| Settings / Notifications | All | ❌ PlaceholderPage | ❓ Endpoint not confirmed |
| Institutions | Admin | ✅ InstitutionsView (assumed) | ✅ CRUD routes |
| Users | Admin | ✅ UsersView (assumed) | ✅ Admin routes |
| AI Providers | Admin | ✅ Card links to route | ✅ providers.py |
| Modules | All (scoped) | ✅ Modules list (assumed) | ✅ Modules routes |
| Programmes | All (scoped) | ✅ Programmes list (assumed) | ✅ Programmes routes |
| Qualification Intelligence | Any | ❓ Not inspected | ⚠️ search 404 |

---

## AI & RAG Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| Multi-provider AI orchestration | ✅ VERIFIED | Gemini, GPT-4, Claude supported |
| SSE streaming responses | ✅ CODE (⚠️ not live-tested in audit) | Route exists |
| Semantic retrieval from Qdrant | ❌ BROKEN | Hash embeddings; `is_placeholder_mode: true` |
| Citation generation | ⚠️ UI complete; retrieval broken | Citations generated; relevance unverified |
| Grounding score | ⚠️ UI complete; score unreliable | LLM self-reports; not computed from retrieval |
| Conversation history | ⚠️ DB tables exist; not tested | AI chat tables migrated |
| SA University Registry | ✅ VERIFIED | 26 institutions; ADIP data |

---

## Security Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| httpOnly cookie tokens | ✅ VERIFIED | Browser JS cannot access tokens |
| No direct FastAPI calls from browser | ✅ VERIFIED | All calls via `/api/proxy/` |
| API keys not in git | ✅ VERIFIED | `.env` in `.gitignore`; no keys in committed files |
| RBAC on all protected routes | ✅ VERIFIED | FastAPI role guards + Next.js middleware |
| Tenant isolation on all queries | ✅ VERIFIED | Service layer enforces `institution_id` scope |

---

## Quality Gate Requirements

| Gate | Last Result | Date |
|------|-------------|------|
| `npx tsc --noEmit` | 0 errors ✅ | 2026-07-12 |
| `npx next lint` | 0 warnings ✅ | 2026-07-12 |
| `npx next build` | Clean ✅ | 2026-07-12 |
| `python -m pytest -q` | 1,198 passed ✅ | 2026-07-12 |
