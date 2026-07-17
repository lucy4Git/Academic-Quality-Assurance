# AQAA Phase D — Component Inventory

**Date:** 2026-07-17

---

## Backend Components

### Routes (`backend/app/routes/`)

| File | Prefix | Description |
|------|--------|-------------|
| `ai_assistant.py` | `/ai-assistant` | Chat sessions, ask-stream, attach, artifacts |
| `artifacts.py` | `/ai-assistant` | Artifact CRUD, archive, restore, export |
| `audits.py` | `/audits` | Module folder audit trigger + results |
| `assessment_audits.py` | `/assessment-audits` | Assessment compliance agent |
| `moderation_audits.py` | `/moderation-audits` | Moderation compliance agent |
| `attendance_audits.py` | `/attendance-audits` | Attendance compliance agent |
| `evidence_audits.py` | `/evidence-audits` | Evidence verification agent |
| `outcome_alignment_audits.py` | `/outcome-alignment-audits` | Outcome alignment agent |
| `accreditation_readiness_audits.py` | `/accreditation-readiness-audits` | Accreditation readiness agent |
| `programme_review_audits.py` | `/programme-review-audits` | Programme review agent |
| `auth.py` | `/auth` | Login, refresh, profile |
| `files.py` | `/files` | File upload, download |
| `institutions.py` | `/institutions` | Institution CRUD |
| `faculties.py` | `/faculties` | Faculty CRUD |
| `departments.py` | `/departments` | Department CRUD |
| `programmes.py` | `/programmes` | Programme CRUD |
| `modules.py` | `/modules` | Module CRUD |
| `users.py` | `/users` | User management |
| `findings.py` | `/findings` | Finding lifecycle |
| `regulatory.py` | `/regulatory` | Regulatory framework queries |

### Services (`backend/app/services/`)

| File | Purpose |
|------|---------|
| `context_engine.py` | Resolve module/programme from query |
| `orchestration_registry.py` | Map intent → action handler |
| `request_planner.py` | Intent detection, confirmation gate |
| `file_service.py` | File content retrieval |
| `embedding_service.py` | Generate embeddings |
| `knowledge_service.py` | Vector search and retrieval |

### RAG (`backend/app/rag/`)

| File | Purpose |
|------|---------|
| `advanced_rag_service.py` | Multi-source retrieval, re-ranking, source records with entity_id/institution_id |

### Parsers (`backend/app/parsers/`)

| File | MIME types |
|------|-----------|
| `pdf_parser.py` | `application/pdf` |
| `docx_parser.py` | `application/vnd.openxmlformats-officedocument...` |
| `txt_parser.py` | `text/plain`, `text/csv` |
| `zip_parser.py` | `application/zip`, `application/x-zip-compressed`, `application/x-zip`, `multipart/x-zip`, `application/octet-stream` |
| `factory.py` | `get_parser(mime)`, `is_supported(mime)` |

### Agents (`backend/app/agents/`)

| Agent | File | Trigger |
|-------|------|---------|
| Module Folder Audit | `module_folder_audit.py` | `POST /audits/modules/{id}/trigger` |
| Assessment Compliance | `assessment_compliance.py` | `POST /assessment-audits/modules/{id}/trigger` |
| Moderation Compliance | `moderation_compliance.py` | `POST /moderation-audits/modules/{id}/trigger` |
| Attendance Compliance | `attendance_compliance.py` | `POST /attendance-audits/modules/{id}/trigger` |
| Evidence Verification | `evidence_verification.py` | `POST /evidence-audits/modules/{id}/trigger` |
| Outcome Alignment | `outcome_alignment.py` | `POST /outcome-alignment-audits/modules/{id}/trigger` |
| Accreditation Readiness | `accreditation_readiness.py` | `POST /accreditation-readiness-audits/modules/{id}/trigger` |
| Programme Review | `programme_review.py` | `POST /programme-review-audits/programmes/{id}/trigger` |

### Models (`backend/app/models/`)

| Model | Table |
|-------|-------|
| `Institution` | `institutions` |
| `Faculty` | `faculties` |
| `Department` | `departments` |
| `Programme` | `programmes` |
| `Module` | `modules` |
| `User` | `users` |
| `File` | `files` |
| `AuditRun` | `audit_runs` |
| `AuditFinding` | `audit_findings` |
| `FindingStatusHistory` | `finding_status_history` |
| `AiChatSession` | `ai_chat_sessions` |
| `AiChatMessage` | `ai_chat_messages` |
| `AiArtifact` | `ai_artifacts` |
| `AiAction` | `ai_actions` |
| `QualityFramework` | `quality_frameworks` |
| `FrameworkVersion` | `framework_versions` |
| `FrameworkStandard` | `framework_standards` |
| `FrameworkCriterion` | `framework_criteria` |

---

## Frontend Components

### Pages (`frontend/src/app/(main)/`)

| Route | File | Description |
|-------|------|-------------|
| `/ai-workspace` | `AiWorkspaceView.tsx` | Main AI workspace |
| `/dashboard` | `page.tsx` | Dashboard overview |
| `/library` | `LibraryPage.tsx` | Library of documents |
| `/knowledge` | `page.tsx` | Knowledge base browser |

### Components

| Component | File | Purpose |
|-----------|------|---------|
| `ArtifactPanel` | `components/ai/ArtifactPanel.tsx` | Artifact CRUD, archive/restore, export |
| `RoleGuard` | `components/auth/RoleGuard.tsx` | Render by role |
| `SessionSidebar` | in `AiWorkspaceView.tsx` | Session list, pin/rename/archive |
| `PromptComposer` | in `AiWorkspaceView.tsx` | Chat input, attach, send |
| `MessageBubble` | in `AiWorkspaceView.tsx` | User/assistant messages |

### Hooks

| Hook | File | Purpose |
|------|------|---------|
| `useAiAssistant` | `hooks/useAiAssistant.ts` | SSE stream management |
| `useAuth` | `hooks/useAuth.ts` | Session rehydration via TanStack Query |
| `useRole` | `hooks/useRole.ts` | Conditional rendering by role |

### API Layer

| File | Purpose |
|------|---------|
| `lib/api/ai-assistant.ts` | All AI workspace API calls + types |
| `lib/api/auth.ts` | Auth API calls |
| `lib/api/files.ts` | File upload API calls |

---

## Database Tables (58 total)

See `database/snapshots/phase-d/aqaa_phase_d_schema.sql` for full DDL.

Key Phase D tables:

| Table | Rows | Purpose |
|-------|------|---------|
| `ai_chat_sessions` | 25+ | Conversation sessions |
| `ai_chat_messages` | 50+ | Messages with citations, structured_blocks, attached_file_ids |
| `ai_artifacts` | — | Artifacts linked to conversations |
| `ai_actions` | — | Dispatched actions from orchestration |
| `audit_findings` | — | Findings with 8-state lifecycle |
| `finding_status_history` | — | Audit trail of finding transitions |

---

## Migrations (21 total)

| # | Revision | Description |
|---|---------|-------------|
| 1 | `99c7b97c9a76` | Initial schema |
| 2 | `bcb42a8b6462` | Add programme QA fields |
| 3 | `6bcc7db53782` | Add module audit tables |
| 4 | `a1afe7223e2a` | Add audit evidence table |
| 5 | `146ff3d10cd9` | Add audit history table |
| 6 | `2a7b17360d01` | Phase 5 workflow comments notifications |
| 7 | `7c5db84357e3` | Add ADIP registry tables |
| 8 | `b0df78d4b8ec` | Add knowledge review tables |
| 9 | `a1b2c3d4e5f6` | Add institution is_active |
| 10 | `c4d5e6f7a8b9` | Add AI chat tables |
| 11 | `e6f7a8b9c0d1` | Add user registration fields |
| 12 | `d5e6f7a8b9c0` | Add qualification tables |
| 13 | `f7a8b9c0d1e2` | Add institution registry fields |
| 14 | `b2c3d4e5f6a7` | Add institutional knowledge foundation |
| 15 | `c3d4e5f6a7b8` | Add acquisition engine |
| 16 | `d4e5f6a7b8c9` | Add extraction engine |
| 17 | `39b2fec2e97f` | Add finding status and history table |
| 18 | `7a8b9c0d1e2f` | Canonical finding status lifecycle |
| 19 | `a1b2c3d4e5f7` | Phase C regulatory framework engine |
| 20 | `51694630069f` | Add source_status to regulatory tables |
| 21 | `7602e7b39d25` | Phase D artifacts, actions, session extensions |
