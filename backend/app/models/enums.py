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
    """Lifecycle status of an audit finding (10-state machine).

    Transitions:
      open → acknowledged | closed_no_action
      acknowledged → in_progress | deferred | escalated
      in_progress → evidence_submitted | deferred | escalated
      evidence_submitted → under_review
      under_review → resolved | rejected
      rejected → in_progress
      deferred → in_progress | escalated
      escalated → in_progress | resolved
      resolved (terminal)
      closed_no_action (terminal)
    """

    OPEN = "open"                         # finding raised by AI agent
    ACKNOWLEDGED = "acknowledged"         # institution acknowledged
    IN_PROGRESS = "in_progress"           # corrective action underway
    EVIDENCE_SUBMITTED = "evidence_submitted"  # evidence uploaded for review
    UNDER_REVIEW = "under_review"         # QA officer reviewing submitted evidence
    RESOLVED = "resolved"                 # finding closed, satisfactory
    REJECTED = "rejected"                 # corrective action insufficient, rework needed
    DEFERRED = "deferred"                 # deferred to next academic cycle
    ESCALATED = "escalated"              # escalated to dean/head of department
    CLOSED_NO_ACTION = "closed_no_action"  # closed without corrective action (INFO)


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
