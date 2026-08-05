"""Shared enumerations used across ORM models."""

import enum


class UserRole(str, enum.Enum):
    """Roles defined in the AQAA requirements (see SRS section 3 - Main Users).

    Stored as a native PostgreSQL enum. Inherits `str` so values serialize
    cleanly through Pydantic schemas and JSON responses without extra coercion.
    """

    SYSTEM_ADMIN = "system_admin"
    QUALITY_ASSURANCE_OFFICER = "quality_assurance_officer"
    FACULTY_DEAN = "faculty_dean"
    HEAD_OF_DEPARTMENT = "head_of_department"
    PROGRAMME_COORDINATOR = "programme_coordinator"
    LECTURER = "lecturer"
    STUDENT = "student"


class InvitationType(str, enum.Enum):
    """Discriminator for secure institutional invitations.

    Each value maps to a specific role/access pattern enforced by
    invitation_service.  Public users never select an invitation type —
    it is embedded in the invitation record created by an authorised admin.
    """

    STUDENT_ONBOARDING = "student_onboarding"       # link personal-email student to institution
    STAFF_LECTURER = "staff_lecturer"               # → role=lecturer
    STAFF_COORDINATOR = "staff_coordinator"         # → role=programme_coordinator
    STAFF_HOD = "staff_hod"                         # → role=head_of_department
    STAFF_DEAN = "staff_dean"                       # → role=faculty_dean
    QA_OFFICER = "qa_officer"                       # → role=quality_assurance_officer
    EXTERNAL_MODERATOR = "external_moderator"       # scoped external access (role=lecturer)
    INSTITUTION_ADMIN = "institution_admin"         # system-admin–only; not public


class InvitationStatus(str, enum.Enum):
    """Lifecycle status of an invitation record."""

    PENDING = "pending"
    CONSUMED = "consumed"   # max_uses reached
    EXPIRED = "expired"     # past expires_at
    REVOKED = "revoked"     # manually cancelled by admin


class ProgrammeLevel(str, enum.Enum):
    """Academic level of a programme, used for reporting and audit scoping."""

    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    DOCTORAL = "doctoral"


class FileCategory(str, enum.Enum):
    """Document category within a module folder.

    Values mirror the document types that each AI audit agent checks for
    (SRS sections 4.4 – 4.10).  Every uploaded file must be assigned one.

    Stage 7 additions (Module Folder Audit Agent required checklist):
        STUDY_GUIDE           — Standalone study / module guide document.
        LEARNING_OUTCOMES     — Explicit learning-outcomes document.
        WEEKLY_PLAN           — Weekly content / teaching schedule.
        ASSESSMENT_PLAN       — Semester-level assessment plan.
        MARK_SHEET            — Grade / mark register (distinct from MARKED_SAMPLE).
    """

    COURSE_OUTLINE = "course_outline"
    STUDY_GUIDE = "study_guide"
    LEARNING_OUTCOMES = "learning_outcomes"
    WEEKLY_PLAN = "weekly_plan"
    ASSESSMENT_PLAN = "assessment_plan"
    ASSESSMENT_BRIEF = "assessment_brief"
    ASSESSMENT_RUBRIC = "assessment_rubric"
    ASSESSMENT_MEMO = "assessment_memo"
    EXAM_PAPER = "exam_paper"
    PRACTICAL_TASK = "practical_task"
    MARKED_SAMPLE = "marked_sample"
    MARK_SHEET = "mark_sheet"
    INTERNAL_MODERATION = "internal_moderation"
    EXTERNAL_MODERATION = "external_moderation"
    MODERATION_EVIDENCE = "moderation_evidence"
    ATTENDANCE_REGISTER = "attendance_register"
    TUTORIAL_ATTENDANCE = "tutorial_attendance"
    PRACTICAL_ATTENDANCE = "practical_attendance"
    LMS_PARTICIPATION = "lms_participation"
    STUDENT_FEEDBACK = "student_feedback"
    ACCREDITATION_EVIDENCE = "accreditation_evidence"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    """Lifecycle state of a document's text-extraction and classification pass.

    PENDING     — record created, processing not yet started.
    PROCESSING  — extraction or classification is actively running.
    COMPLETED   — text extracted and document classified successfully.
    FAILED      — an unrecoverable error occurred; error_message is set.
    SKIPPED     — format is not parseable (e.g. password-protected PDF).
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, enum.Enum):
    """Discriminator that identifies which AI audit agent produced an AuditRun.

    Adding new agents in future stages: add a value here and set it when
    creating the AuditRun in the agent's service module.
    """

    MODULE_FOLDER_AUDIT = "module_folder_audit"
    ASSESSMENT_COMPLIANCE = "assessment_compliance"
    MODERATION_COMPLIANCE = "moderation_compliance"
    ATTENDANCE_COMPLIANCE = "attendance_compliance"
    EVIDENCE_VERIFICATION = "evidence_verification"
    OUTCOME_ALIGNMENT = "outcome_alignment"
    ACCREDITATION_READINESS = "accreditation_readiness"
    PROGRAMME_REVIEW = "programme_review"


class AuditStatus(str, enum.Enum):
    """Overall compliance status derived from the audit compliance score.

    COMPLIANT       — score ≥ 90 %.  All critical documents present.
    NEEDS_ATTENTION — score 70 – 89 %.  Some important documents missing.
    NON_COMPLIANT   — score 50 – 69 %.  Several required documents missing.
    CRITICAL        — score < 50 %.  Major QA deficiencies; immediate action needed.
    """

    COMPLIANT = "compliant"
    NEEDS_ATTENTION = "needs_attention"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"


class AuditRunStatus(str, enum.Enum):
    """Lifecycle state of an audit run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverity(str, enum.Enum):
    """Severity level of an individual audit finding."""

    CRITICAL = "critical"   # mandatory document absent
    HIGH = "high"           # important document absent
    MEDIUM = "medium"       # recommended document absent
    LOW = "low"             # minor issue or improvement suggestion
    INFO = "info"           # informational (e.g. reclassification suggestion)


class FindingType(str, enum.Enum):
    """Type of audit finding."""

    MISSING_DOCUMENT = "missing_document"
    MISCLASSIFIED = "misclassified"
    QUALITY_ISSUE = "quality_issue"
    RECOMMENDATION = "recommendation"
    INFO = "info"


class FindingStatus(str, enum.Enum):
    """Canonical lifecycle status of an audit finding (12-state machine).

    OPEN              → ACKNOWLEDGED | ASSIGNED | ESCALATED | CLOSED
    ACKNOWLEDGED      → ASSIGNED | IN_PROGRESS | DEFERRED | ESCALATED
    ASSIGNED          → IN_PROGRESS | DEFERRED | ESCALATED
    IN_PROGRESS       → RESOLUTION_SUBMITTED | DEFERRED | ESCALATED
    RESOLUTION_SUBMITTED → UNDER_REVIEW | IN_PROGRESS (retracted)
    UNDER_REVIEW      → RESOLVED | REJECTED
    REJECTED          → IN_PROGRESS | ESCALATED
    RESOLVED          → REOPENED | CLOSED
    REOPENED          → ASSIGNED | IN_PROGRESS
    ESCALATED         → IN_PROGRESS | UNDER_REVIEW | RESOLVED
    DEFERRED          → IN_PROGRESS | ESCALATED
    CLOSED            (terminal)

    ACKNOWLEDGED: institution has formally acknowledged the finding exists,
      before a coordinator assigns it. ASSIGNED: explicitly allocated to an
      individual for remediation. These are distinct — acknowledgement is a
      governance gate; assignment is a workflow action.
    DEFERRED: postponed to the next academic cycle (retained from earlier
      implementation as a valid and regularly used state).
    CLOSED: finding closed with or without corrective action (replaces the
      former CLOSED_NO_ACTION). The note field records the reason.
    """

    OPEN = "open"                               # finding raised by AI agent
    ACKNOWLEDGED = "acknowledged"               # institution acknowledged finding
    ASSIGNED = "assigned"                       # allocated to responsible person
    IN_PROGRESS = "in_progress"                 # corrective action underway
    RESOLUTION_SUBMITTED = "resolution_submitted"  # evidence/resolution uploaded
    UNDER_REVIEW = "under_review"               # QA officer reviewing submission
    RESOLVED = "resolved"                       # finding closed satisfactorily
    REJECTED = "rejected"                       # submission rejected — rework required
    REOPENED = "reopened"                       # previously resolved; new evidence needed
    ESCALATED = "escalated"                     # escalated to dean / HOD
    DEFERRED = "deferred"                       # deferred to next academic cycle
    CLOSED = "closed"                           # closed — note records reason


class AttendanceRiskLevel(str, enum.Enum):
    """Risk level for module attendance evidence (Attendance Compliance Agent).

    Derived from weekly attendance-evidence completeness percentage and the
    overall attendance compliance score (worse-of-both):

    LOW       — completeness >= 90%. Attendance evidence is essentially complete.
    MEDIUM    — completeness 70-89%. Some weeks/documents missing.
    HIGH      — completeness 50-69%. Significant gaps in attendance evidence.
    CRITICAL  — completeness < 50%. Attendance evidence is largely absent.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceRiskLevel(str, enum.Enum):
    """Risk level for module evidence completeness (Evidence Verification Agent).

    Derived from the evidence completeness percentage (presence-checklist
    coverage across assessment, moderation, attendance, and accreditation
    evidence groups) and the overall evidence verification score
    (worse-of-both):

    LOW       — completeness >= 90%. Evidence base is essentially complete.
    MEDIUM    — completeness 70-89%. Some evidence groups/links missing.
    HIGH      — completeness 50-69%. Significant evidence gaps.
    CRITICAL  — completeness < 50%. Evidence base is largely absent or unverifiable.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlignmentRiskLevel(str, enum.Enum):
    """Risk level for outcome alignment (Outcome Alignment Agent).

    Derived from the module-outcome assessment-coverage percentage and the
    overall outcome alignment score (worse-of-both):

    LOW       — coverage >= 90%. Outcomes are well-defined and well-aligned.
    MEDIUM    — coverage 70-89%. Some outcomes/mappings missing.
    HIGH      — coverage 50-69%. Significant alignment gaps.
    CRITICAL  — coverage < 50%. Outcomes are largely undefined or unaligned.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReadinessRiskLevel(str, enum.Enum):
    """Risk level for accreditation readiness (Accreditation Readiness Agent).

    Derived from the overall readiness score and the number/severity of
    unresolved findings carried over from prior compliance audits
    (worse-of-both):

    LOW       — score >= 90% and no unresolved critical/high findings.
    MEDIUM    — score 70-89%, or some unresolved findings to review.
    HIGH      — score 50-69%, or several unresolved high-severity findings.
    CRITICAL  — score < 50%, or any unresolved critical findings remain.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChecklistItemStatus(str, enum.Enum):
    """Status of a single QA checklist item within a module folder audit."""

    COMPLIANT = "compliant"
    MISSING = "missing"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class ModuleAuditStatus(str, enum.Enum):
    """Overall outcome of a completed module folder audit.

    COMPLIANT     — compliance >= 90 %.  All critical items present.
    AT_RISK       — compliance 70 – 89 %.  Some items missing.
    NON_COMPLIANT — compliance < 70 %.  Critical items missing.
    DRAFT         — audit created but not yet submitted.
    """

    DRAFT = "draft"
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    NON_COMPLIANT = "non_compliant"


class WorkflowStatus(str, enum.Enum):
    """Lifecycle status for module audit workflow."""

    DRAFT = "draft"
    ASSIGNED = "assigned"
    EVIDENCE_COLLECTION = "evidence_collection"
    PENDING_QA_REVIEW = "pending_qa_review"
    RETURNED_FOR_CORRECTIONS = "returned_for_corrections"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AuditPriority(str, enum.Enum):
    """Priority level for an audit assignment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, enum.Enum):
    """Type of in-app notification."""

    AUDIT_ASSIGNED = "audit_assigned"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_MISSING = "evidence_missing"
    AUDIT_RETURNED = "audit_returned"
    AUDIT_APPROVED = "audit_approved"
    AUDIT_REJECTED = "audit_rejected"
    AUDIT_COMPLETED = "audit_completed"
    NEW_COMMENT = "new_comment"


class ReviewItemStatus(str, enum.Enum):
    """Lifecycle status of a single knowledge review item."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    QUARANTINED = "quarantined"
    IMPORTED = "imported"


class ReviewBatchStatus(str, enum.Enum):
    """Lifecycle status of a knowledge review batch."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    EXPORTED = "exported"
    CLOSED = "closed"


class UploadState(str, enum.Enum):
    """Upload lifecycle state.

    PENDING    — file received, not yet scanned.
    SCANNING   — virus/malware scan in progress.
    READY      — scan passed; file is accessible.
    QUARANTINED — scan detected a threat; file is blocked.
    FAILED     — upload or processing error; record preserved for audit.
    """

    PENDING = "pending"
    SCANNING = "scanning"
    READY = "ready"
    QUARANTINED = "quarantined"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Phase C — Regulatory and Quality Framework Engine
# ---------------------------------------------------------------------------


class AuthorityType(str, enum.Enum):
    """Type of regulatory or quality authority."""

    NATIONAL_REGULATOR = "national_regulator"
    QUALIFICATION_AUTHORITY = "qualification_authority"
    QUALITY_COUNCIL = "quality_council"
    PROFESSIONAL_COUNCIL = "professional_council"
    ACCREDITATION_BODY = "accreditation_body"
    GOVERNMENT_DEPARTMENT = "government_department"
    SETA = "seta"
    INSTITUTION = "institution"
    FACULTY = "faculty"
    DEPARTMENT = "department"
    INTERNATIONAL_BODY = "international_body"
    CUSTOM = "custom"


class AuthorityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"


class FrameworkType(str, enum.Enum):
    """Type of quality or accreditation framework."""

    INSTITUTIONAL_AUDIT = "institutional_audit"
    PROGRAMME_ACCREDITATION = "programme_accreditation"
    QUALIFICATION_REGISTRATION = "qualification_registration"
    PROFESSIONAL_ACCREDITATION = "professional_accreditation"
    OCCUPATIONAL_QUALIFICATION = "occupational_qualification"
    ASSESSMENT_POLICY = "assessment_policy"
    MODERATION_POLICY = "moderation_policy"
    TEACHING_AND_LEARNING = "teaching_and_learning"
    WORK_INTEGRATED_LEARNING = "work_integrated_learning"
    CLINICAL_TRAINING = "clinical_training"
    ENGINEERING_EDUCATION = "engineering_education"
    TEACHER_EDUCATION = "teacher_education"
    CUSTOM = "custom"


class FrameworkScope(str, enum.Enum):
    NATIONAL = "national"
    INTERNATIONAL = "international"
    INSTITUTIONAL = "institutional"
    FACULTY = "faculty"
    DEPARTMENT = "department"
    PROGRAMME = "programme"
    MODULE = "module"


class VersionStatus(str, enum.Enum):
    """Lifecycle status of a framework version."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    ARCHIVED = "archived"


class EvaluationMethod(str, enum.Enum):
    """How a criterion is evaluated."""

    DOCUMENT_PRESENCE = "document_presence"
    METADATA_VALIDATION = "metadata_validation"
    RULE_BASED = "rule_based"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    NUMERIC_THRESHOLD = "numeric_threshold"
    MANUAL_REVIEW = "manual_review"
    HYBRID = "hybrid"
    CUSTOM = "custom"


class EvidenceType(str, enum.Enum):
    """Type of evidence required for a criterion."""

    DOCUMENT = "document"
    NUMERIC = "numeric"
    NARRATIVE = "narrative"
    STRUCTURED_DATA = "structured_data"
    SIGNED_DOCUMENT = "signed_document"
    DATED_DOCUMENT = "dated_document"
    PERIODIC = "periodic"
    SAMPLE = "sample"
    HUMAN_VERIFIED = "human_verified"
    CUSTOM = "custom"


class SourceStatus(str, enum.Enum):
    """Provenance status of a regulatory authority, framework, or version record.

    Stored as a plain string column (not a native PG enum) so new values can
    be added without a migration ALTER TYPE statement.
    """

    OFFICIAL_VERIFIED = "OFFICIAL_VERIFIED"
    OFFICIAL_UNVERIFIED = "OFFICIAL_UNVERIFIED"
    INSTITUTIONAL_APPROVED = "INSTITUTIONAL_APPROVED"
    TEST_FIXTURE = "TEST_FIXTURE"
    DRAFT_IMPORT = "DRAFT_IMPORT"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class ApplicabilityTargetType(str, enum.Enum):
    """The type of academic entity an applicability rule targets."""

    INSTITUTION = "institution"
    CAMPUS = "campus"
    FACULTY = "faculty"
    DEPARTMENT = "department"
    QUALIFICATION = "qualification"
    PROGRAMME = "programme"
    MODULE = "module"
    ASSESSMENT = "assessment"
    ANY = "any"


class MappingSource(str, enum.Enum):
    """How an evidence mapping was created."""

    MANUAL = "manual"
    RULE_BASED = "rule_based"
    SEMANTIC_RETRIEVAL = "semantic_retrieval"
    AI_ASSISTED = "ai_assisted"
    IMPORTED = "imported"
    SYSTEM_INFERRED = "system_inferred"


class MappingValidationStatus(str, enum.Enum):
    PROPOSED = "proposed"
    MATCHED = "matched"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class FrameworkAssessmentStatus(str, enum.Enum):
    """Lifecycle status of a framework assessment run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_REVIEW = "requires_review"


class CrossFrameworkRelation(str, enum.Enum):
    """Semantic relationship between two criteria / standards across frameworks."""

    EQUIVALENT = "equivalent"
    PARTIALLY_EQUIVALENT = "partially_equivalent"
    SUPPORTS = "supports"
    OVERLAPS = "overlaps"
    CONFLICTS_WITH = "conflicts_with"
    SUPERSEDES = "supersedes"
    REFERENCES = "references"
    NO_RELATION = "no_relation"


class RegulatoryRisk(str, enum.Enum):
    """Risk level of a regulatory finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Phase D — Artifact Engine
# ---------------------------------------------------------------------------


class ArtifactType(str, enum.Enum):
    """Type of AI-generated artifact produced in the AI Workspace."""

    MODULE_AUDIT_REPORT = "module_audit_report"
    PROGRAMME_COMPLIANCE_REPORT = "programme_compliance_report"
    DEPARTMENT_QUALITY_REPORT = "department_quality_report"
    FACULTY_QUALITY_REPORT = "faculty_quality_report"
    INSTITUTIONAL_QUALITY_REPORT = "institutional_quality_report"
    REGULATORY_READINESS_REPORT = "regulatory_readiness_report"
    ACCREDITATION_EVIDENCE_PACK = "accreditation_evidence_pack"
    CORRECTIVE_ACTION_PLAN = "corrective_action_plan"
    RISK_REGISTER = "risk_register"
    ASSESSMENT_ALIGNMENT_MATRIX = "assessment_alignment_matrix"
    MODERATION_REPORT = "moderation_report"
    EXECUTIVE_BRIEFING = "executive_briefing"
    QA_MEETING_PACK = "qa_meeting_pack"
    EVIDENCE_CHECKLIST = "evidence_checklist"
    FRAMEWORK_COMPARISON = "framework_comparison"
    QUALIFICATION_ALIGNMENT_REPORT = "qualification_alignment_report"


class ArtifactStatus(str, enum.Enum):
    """Lifecycle state of an artifact."""

    DRAFT = "draft"
    SAVED = "saved"
    VERSIONED = "versioned"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ArtifactApprovalStatus(str, enum.Enum):
    """Approval state of an artifact requiring formal sign-off."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionType(str, enum.Enum):
    """Conversational action types executed through the AI Workspace."""

    # Findings
    ACKNOWLEDGE_FINDING = "acknowledge_finding"
    ASSIGN_FINDING = "assign_finding"
    START_PROGRESS = "start_progress"
    SUBMIT_RESOLUTION = "submit_resolution"
    REQUEST_REVIEW = "request_review"
    APPROVE_RESOLUTION = "approve_resolution"
    REJECT_RESOLUTION = "reject_resolution"
    REOPEN_FINDING = "reopen_finding"
    ESCALATE_FINDING = "escalate_finding"
    CLOSE_FINDING = "close_finding"
    ADD_COMMENT = "add_comment"
    SET_DUE_DATE = "set_due_date"
    UPLOAD_RESOLUTION_EVIDENCE = "upload_resolution_evidence"
    # Regulatory
    RUN_FRAMEWORK_ASSESSMENT = "run_framework_assessment"
    RUN_INTEGRATED_READINESS = "run_integrated_readiness"
    PROMOTE_GAPS_TO_FINDINGS = "promote_gaps_to_findings"
    GENERATE_REGULATORY_REPORT = "generate_regulatory_report"
    GENERATE_EVIDENCE_PACK = "generate_evidence_pack"
    CREATE_CORRECTIVE_ACTION_PLAN = "create_corrective_action_plan"
    # Audit
    RUN_MODULE_AUDIT = "run_module_audit"
    RUN_ASSESSMENT_AUDIT = "run_assessment_audit"
    RUN_MODERATION_AUDIT = "run_moderation_audit"
    RUN_ATTENDANCE_AUDIT = "run_attendance_audit"
    RUN_OUTCOME_ALIGNMENT = "run_outcome_alignment"
    VERIFY_EVIDENCE = "verify_evidence"
    # Artifacts
    SAVE_ARTIFACT = "save_artifact"
    REGENERATE_ARTIFACT = "regenerate_artifact"
    EXPORT_ARTIFACT = "export_artifact"
    SHARE_ARTIFACT = "share_artifact"
    ASSIGN_ARTIFACT = "assign_artifact"
    APPROVE_ARTIFACT = "approve_artifact"
    REJECT_ARTIFACT = "reject_artifact"


class ActionStatus(str, enum.Enum):
    """Execution state of a conversational action."""

    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
