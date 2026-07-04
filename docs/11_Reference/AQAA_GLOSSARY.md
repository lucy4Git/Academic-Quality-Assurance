# AQAA — Master Glossary

**Document ID:** REF-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29

This glossary defines all technical, academic, QA, AI, and governance terms used in AQAA.

---

## A

**Academic Year**  
The 12-month period covering a full teaching cycle, typically running February–November in South Africa. In AQAA, academic year is a required field on Module records (e.g., `"2025/2026"`).

**Accreditation**  
The formal process by which a body such as CHE or ECSA certifies that an institution or programme meets defined quality standards. AQAA's Accreditation Readiness Agent checks evidence readiness for accreditation visits.

**Advanced Diploma**  
An NQF Level 7 qualification (minimum 120 credits) that follows a Diploma (NQF 6). Prepares graduates for specialisation or professional registration.

**Agent Type**  
An enum (`AgentType`) identifying which AI agent produced an `AuditRun`. Values: `module_folder_audit`, `assessment_compliance`, `moderation_compliance`, `attendance_compliance`, `evidence_verification`, `outcome_alignment`, `accreditation_readiness`, `programme_review`.

**Alembic**  
The database migration tool used in AQAA. Always invoked as `python -m alembic` (not bare `alembic`) on Windows. Migration files live in `backend/alembic/versions/`.

**APS (Admission Point Score)**  
A South African university admission scoring system calculated from National Senior Certificate results. Life Orientation is excluded. TUT APS ranges: HC ≥ 18, Diploma ≥ 19–26, BEngTech ≥ 28–30. Stored in IKP `admission_requirements` objects.

**asyncpg**  
The async PostgreSQL driver used by AQAA via SQLAlchemy 2. Requires careful handling of PostgreSQL enum type creation (use `DO $$ BEGIN IF NOT EXISTS ... END $$;` blocks in migrations — see LL-0010).

**AT_RISK**  
A `ModuleAuditStatus` value. Applied when `compliance_percentage` is between 70% and 89%. Indicates that some important checklist items are missing.

**Audit History**  
An immutable, append-only log of all significant events affecting a `ModuleAudit`. Stored in the `audit_history` table. Model: `backend/app/models/audit_history.py`.

**Audit Template**  
An IKP object (Layer 4) defining the checklist and compliance thresholds to apply to a specific programme type at a specific NQF level.

**AuditChecklistItem**  
One of 10 fixed checklist criteria within a `ModuleAudit`. Status options: `compliant`, `missing`, `partial`, `not_applicable`.

**AuditEvidence**  
A model representing a file uploaded as evidence for a specific checklist item in a module audit. Stored in `evidence/{institution_id}/{audit_id}/{uuid}{ext}`.

**AuditFinding**  
A specific compliance issue identified by an AI agent during an `AuditRun`. Has severity (`critical`, `high`, `medium`, `low`, `info`) and type (`missing_document`, `quality_issue`, `recommendation`, `info`).

**AuditRun**  
A record of one AI agent execution against a module or programme. Created with status `pending`, updated to `completed` or `failed` by the agent.

**AuditRunStatus**  
Enum for AI agent run lifecycle: `pending`, `running`, `completed`, `failed`. Stored as plain `str` in PostgreSQL — do **not** call `.value` on it.

---

## B

**Base-UI**  
The `@base-ui/react` library used for ShadCN UI components in AQAA. **Different from Radix UI.** The `asChild` prop does **not** exist. Use `buttonVariants()` + `<Link>` for link-buttons.

**Bearer Token**  
The JWT access token sent as `Authorization: Bearer {token}` by the Next.js API proxy to FastAPI. The browser never sees or sends this directly.

**bcrypt**  
The password hashing algorithm used in AQAA (`backend/app/security.py`).

---

## C

**Campus**  
A physical location where an institution operates. One institution can have multiple campuses. In TUT IKP: Soshanguve South (primary for ICT), eMalahleni, Polokwane.

**CHE (Council on Higher Education)**  
South Africa's quality assurance body for higher education. Responsible for programme accreditation. All AQAA-audited programmes must have CHE accreditation to be valid for loading.

**ChecklistItemStatus**  
Enum for a single QA checklist item: `compliant`, `missing`, `partial`, `not_applicable`. Stored as native PostgreSQL enum `checklist_item_status`.

**Compliance Percentage**  
Calculated as: `(compliant_count + partial_count × 0.5) / (total_items − not_applicable_count) × 100`. Drives the audit status (COMPLIANT / AT_RISK / NON_COMPLIANT).

**COMPLIANT**  
A `ModuleAuditStatus` value. Applied when `compliance_percentage ≥ 90%`. All critical items present.

**Confidence Score**  
A float (0.0–1.0) assigned to every field of every IKP knowledge object. Determines whether data is auto-loaded (≥ 0.85), flagged for review (0.70–0.84), or blocked (<0.70). See ADR-0006.

**CoordinatorRequired**  
A named FastAPI dependency shortcut in `backend/app/dependencies.py`. Allows access to users with role `PROGRAMME_COORDINATOR` and above. Used directly as a default value — never wrapped in `Depends()`.

---

## D

**Department**  
The third level of the AQAA institutional hierarchy (Institution → Faculty → **Department** → Programme → Module). Has optional `head_id` linking to a user.

**Depends()**  
FastAPI's dependency injection mechanism. Named role shortcuts in AQAA (`CoordinatorRequired`, `QAOfficerRequired`, etc.) are already `Depends()` objects — **never** wrap them in additional `Depends()` calls (causes `TypeError` in FastAPI 0.136.3+).

**DHET (Department of Higher Education and Training)**  
South African government department responsible for higher education policy. Approves institution and programme inclusion on the PQM (Programme Qualification Mix).

**Doctor of Computing**  
An NQF Level 10 qualification (360 credits) offered by TUT's Faculty of ICT across all 4 departments. The highest level in the ICT progression.

**Draft**  
Initial `ModuleAuditStatus` and `WorkflowStatus`. A newly created audit before any checklist items are set.

---

## E

**ECSA (Engineering Council of South Africa)**  
Professional registration body for engineers. Diplomas enable registration as professional engineering technicians; BEngTech enables registration as professional engineering technologists.

**ECP (Extended Curriculum Programme)**  
A variant of certain TUT programmes that accepts students with lower APS (typically 3 points below standard). Not confirmed on official TUT HTML pages — pending ICT Prospectus PDF extraction.

**Evidence**  
A file uploaded to AQAA and linked to a specific `AuditChecklistItem`. Stored in local file system (development) or cloud storage (future). Supported preview types: PDF, PNG, JPG, GIF, WebP, SVG, TXT, CSV.

**Extraction Method**  
How a piece of data was obtained for an IKP record. Values: `web_fetch_automated`, `pdf_text_extract`, `ocr`, `manual_entry`. Stored in provenance records.

---

## F

**Faculty**  
The second level of the AQAA institutional hierarchy (Institution → **Faculty** → Department → Programme → Module). Model: `backend/app/models/faculty.py`. **Important:** explicit `__tablename__ = "faculties"` — SQLAlchemy's auto-pluralisation produces `"facultys"` (incorrect).

**FastAPI**  
The Python web framework used for AQAA's backend API. Version 0.136.3+. Key pattern: named dependency shortcuts are `Depends()` objects used directly as default parameter values.

**FileCategory**  
Enum (`str`) representing the type of document uploaded. Values include: `course_outline`, `study_guide`, `assessment_brief`, `internal_moderation`, `marked_sample`, `attendance_register`, etc. Used to classify evidence files.

**Finding**  
See `AuditFinding`.

---

## G

**GFU (Greenfield University)**  
Demo institution in AQAA. Not a real university — created for development and testing. Institution code: `GFU`. All GFU data originates from `database/seed_data/seed.py`.

**Graduate Attributes**  
Overarching capabilities a programme is designed to develop in students (e.g., critical thinking, communication, ethical reasoning). Part of the Curriculum Layer (Layer 3) of the IKP.

---

## H

**HEQSF (Higher Education Qualifications Sub-Framework)**  
The sub-framework under SAQA's NQF that specifies minimum credit requirements per qualification type. Used in AQAA to provide HEQSF-standard credit values when institution-specific values are not yet confirmed.

**HOD (Head of Department)**  
A user role in AQAA (`HEAD_OF_DEPARTMENT`). Manages department-level QA. Has access to modules and programmes within their department.

**httpOnly Cookie**  
A browser cookie that JavaScript cannot access. AQAA stores JWT tokens exclusively in httpOnly cookies for security. The Next.js API proxy reads this cookie server-side and injects the Bearer header.

---

## I

**IKP (Institutional Knowledge Package)**  
A version-controlled, provenance-tagged JSON package encoding everything AQAA needs to know about an institution. Contains 8 layers from Institution to Metadata. Every field has a confidence score. Sealed versions are immutable. See ADR-0004 and `docs/10_Knowledge_Base/`.

**IKP Assembly**  
Stage 7 of the IKP ingestion pipeline. Builds the complete IKP directory tree, attaches provenance, computes SHA-256 seal hash, and sets status to `sealed`.

**IKP Seal**  
A SHA-256 hash of all files in a sealed IKP version, computed at seal time. Allows verification that a sealed IKP has not been modified.

**Institution**  
The root tenant entity in AQAA. Every other entity (Faculty, Department, Programme, Module, User, Audit) is scoped to exactly one Institution via `institution_id`. Model: `backend/app/models/institution.py`.

**institution_id**  
The UUID foreign key that links every data record to its tenant institution. Must be present on all data tables. Enforced in the service layer for all multi-tenant queries.

---

## J

**JWT (JSON Web Token)**  
The token format used for AQAA authentication. Signed with HS256 algorithm using `SECRET_KEY`. Access token expires in 60 minutes; refresh token in 7 days. Never stored in JavaScript-accessible storage.

---

## L

**Learning Outcome**  
A specific, measurable statement of what a student will be able to do, know, or demonstrate upon completing a module. Part of the Curriculum Layer (Layer 3) of the IKP. Used by the Outcome Alignment Agent to verify assessment-outcome mapping.

**Lecturer**  
A user role in AQAA (`LECTURER`). Can upload evidence, view their assigned modules' audit status. Cannot approve, assign, or manage workflow for audits they're not assigned to.

**Life Orientation**  
A compulsory NSC subject excluded from APS calculation at TUT (and most South African universities). Must be excluded when calculating APS from NSC results.

---

## M

**Moderation**  
The process of verifying that assessment standards are appropriate and consistently applied. In AQAA context, internal moderation reports are a required checklist item. The Moderation Compliance Agent checks for moderation documentation.

**Module**  
The lowest level of the AQAA institutional hierarchy at which QA audits operate. Has `programme_id`, `code`, `name`, `credits`, `semester`, `academic_year`, `lecturer_id`. Identified uniquely by `(programme_id, code, academic_year)`.

**ModuleAudit**  
A manual QA audit of a module's folder. Contains a fixed set of 10 `AuditChecklistItem` rows. Compliance percentage drives status. Distinct from the AI-driven `AuditRun`.

**ModuleAuditStatus**  
Enum for manual audit outcomes: `draft`, `compliant`, `at_risk`, `non_compliant`. Separate from `WorkflowStatus`.

**Multi-Tenancy**  
AQAA's shared-database, row-level tenant isolation architecture. Every data row is scoped to an `institution_id`. System Admins bypass tenant filters. See ADR-0002.

---

## N

**NON_COMPLIANT**  
A `ModuleAuditStatus` value. Applied when `compliance_percentage < 70%`. Critical documents missing.

**Notification**  
An in-app message generated by AQAA workflow events. 10 types: `audit_assigned`, `due_soon`, `overdue`, `evidence_uploaded`, `evidence_missing`, `audit_returned`, `audit_approved`, `audit_rejected`, `audit_completed`, `new_comment`. Stored in `notifications` table.

**NQF (National Qualifications Framework)**  
South Africa's 10-level framework for classifying qualifications. Managed by SAQA. Level 5 = HC; Level 6 = Diploma; Level 7 = Adv Diploma / Bachelor's; Level 8 = PGDip / Honours; Level 9 = Master's; Level 10 = Doctorate.

**NSC (National Senior Certificate)**  
The South African Grade 12 school-leaving certificate. The primary admission qualification for undergraduate study. Used to calculate APS.

---

## P

**pdfminer.six**  
The Python library designated for PDF text extraction in AQAA. Pure Python — no system dependencies (unlike pdftoppm which requires Poppler). Required for Phase 5.4D PDF extraction task. Install: `pip install pdfminer.six`.

**PGDip (Postgraduate Diploma)**  
An NQF Level 8 qualification (minimum 120 credits). Typically requires a prior Diploma (NQF 6) as entry requirement.

**POPIA (Protection of Personal Information Act)**  
South African data protection law. AQAA stores minimum necessary PII. Users are deactivated (not deleted); their data is anonymised after 90 days post-deactivation.

**Programme**  
The fourth level of the AQAA institutional hierarchy. A named academic programme (e.g., "Diploma in Computer Science") with NQF level, credits, and duration. Model: `backend/app/models/programme.py`.

**Programme Review Agent**  
The only programme-scoped AI agent in AQAA (all others are module-scoped). Triggered via `POST /api/v1/programme-review-audits/programmes/{id}/trigger`.

**Provenance**  
The traceable chain from an AQAA data record back to its authoritative source. Every IKP field has a provenance record containing: source type, URL, document, page number, extraction date, confidence score, verifier. See ADR-0006.

**Provenance Envelope**  
The JSON object attached to every IKP knowledge object containing all provenance metadata. Mandatory — objects without provenance cannot be loaded into AQAA.

---

## Q

**QA (Quality Assurance)**  
The processes and systems that ensure academic programmes meet established standards for content, delivery, assessment, and outcomes.

**QAO (Quality Assurance Officer)**  
AQAA role (`QUALITY_ASSURANCE_OFFICER`). Can approve/reject/return audits. Has access to all audit functions for their institution. Reports to System Admin.

**Qdrant**  
The vector database used by AQAA for AI agent embeddings. Runs in Docker container `aqaa-qdrant` on ports 6333 (REST) and 6334 (gRPC). Healthcheck uses `bash -c '</dev/tcp/localhost/6333'`.

---

## R

**RBAC (Role-Based Access Control)**  
AQAA's permission system. Seven roles in cumulative hierarchy: `SYSTEM_ADMIN → QUALITY_ASSURANCE_OFFICER → FACULTY_DEAN → HEAD_OF_DEPARTMENT → PROGRAMME_COORDINATOR → LECTURER → STUDENT`. Enforced in `backend/app/dependencies.py` (API) and `frontend/src/middleware.ts` (routing).

**RCT (Riverside College of Technology)**  
Demo institution in AQAA. Not a real institution. Created for development and testing. Data from `database/seed_data/seed_extended.py`.

**Redis**  
AQAA's caching layer. Docker container `aqaa-redis` on port 6379.

**RoleGuard**  
A React client component (`frontend/src/components/auth/RoleGuard.tsx`) that renders children only when the current user's role is in the allowed list. Uses `roles` prop (not `allowed`).

**RPL (Recognition of Prior Learning)**  
A process allowing students with prior experience or non-formal learning to gain credit towards a qualification. Part of the Institutional Policy Layer (Layer 6) of the IKP.

**run_id**  
The UUID returned immediately when an AI agent is triggered (HTTP 202). Used to poll `GET /api/v1/audits/{run_id}` for completion status.

---

## S

**SAQA (South African Qualifications Authority)**  
Responsible for the NQF and registering qualifications. All TUT programmes must be SAQA-registered before they can be loaded into AQAA as authoritative data.

**Sealed**  
The final state of an IKP version. A sealed IKP is immutable — its SHA-256 hash is computed and stored. No files in a sealed version may be modified. See ADR-0006.

**Secondary Source**  
A non-official website (e.g., briefly.co.za, studychoices.org.za) that aggregates or summarises institutional data. Data from secondary sources has confidence score 0.45 and must not be loaded into AQAA.

**Seed Data**  
Demonstration data generated by `database/seed_data/run_all.py`. Creates GFU and RCT institutions with a realistic multi-institution hierarchy. All seeded users share password `ChangeMe123!`.

**SQLAlchemy 2**  
The async ORM used in AQAA. Key usage: `AsyncSession`, `select()` statements, `selectinload()` for relationships, `Mapped` + `mapped_column()` for type-annotated models.

**System Admin**  
AQAA role (`SYSTEM_ADMIN`). Has full platform access. Bypasses tenant isolation (`institution_id` filter). Should be used only for platform administration.

---

## T

**TanStack Query**  
The server state management library used in the AQAA frontend. Provides `useQuery`, `useMutation`, `useQueryClient` for API data fetching, caching, and invalidation.

**Tenant**  
One institution in AQAA's multi-tenant system. Each institution is a completely isolated tenant. Data from one tenant cannot be accessed by users of another tenant (except System Admin).

**Tshwane University of Technology (TUT)**  
South Africa's largest university of technology (60,000+ students, 7 faculties). The first real-world pilot institution for AQAA. Only standalone Faculty of ICT in South Africa. Established 2004. See ADR-0003.

**TSB (Tshwane School for Business and Society)**  
TUT's business school, accredited for PDBA, MBA, and DBA. Has its own domain: `tsb.ac.za`.

---

## U

**UNISA**  
University of South Africa. Distance education institution planned for AQAA onboarding in Phase 7+. Has 3,000+ modules — requires mature platform before onboarding.

---

## V

**Versioning**  
AQAA uses semantic versioning for IKP packages: `MAJOR.MINOR.PATCH` where MAJOR = new academic year, MINOR = new content added, PATCH = corrections. All versions are preserved permanently. See ADR-0006.

---

## W

**WIL (Work-Integrated Learning)**  
An assessment or qualification component requiring students to demonstrate competencies in a real or simulated workplace. Mandatory in most TUT programmes. Employer communication and student progress documentation are required by WIL policy.

**Workflow**  
AQAA's 9-state lifecycle for module audits: `Draft → Assigned → Evidence Collection → Pending QA Review → [Approved | Rejected | Returned for Corrections] → Completed → Archived`. Enforced by `backend/app/services/workflow_service.py`.

**WorkflowStatus**  
Enum for the 9 workflow states. Stored as PostgreSQL enum type `workflow_status`. A column on `ModuleAudit` model.

---

## Z

**Zustand**  
The client-side state management library used for the AQAA auth store (`frontend/src/store/auth.store.ts`). Stores the current user object and authentication state.

---

*Add new terms alphabetically. Cross-reference related terms using `See [term]` notation.*
