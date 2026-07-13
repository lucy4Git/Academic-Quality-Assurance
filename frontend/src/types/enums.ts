// Mirrors backend app/models/enums.py — all string enums

export type UserRole =
  | "system_admin"
  | "quality_assurance_officer"
  | "faculty_dean"
  | "head_of_department"
  | "programme_coordinator"
  | "lecturer"
  | "student";

export type ProgrammeLevel = "undergraduate" | "postgraduate" | "doctoral";

export type FileCategory =
  | "course_outline"
  | "study_guide"
  | "learning_outcomes"
  | "weekly_plan"
  | "assessment_plan"
  | "assessment_brief"
  | "assessment_rubric"
  | "assessment_memo"
  | "exam_paper"
  | "practical_task"
  | "marked_sample"
  | "mark_sheet"
  | "internal_moderation"
  | "external_moderation"
  | "moderation_evidence"
  | "attendance_register"
  | "tutorial_attendance"
  | "practical_attendance"
  | "lms_participation"
  | "student_feedback"
  | "accreditation_evidence"
  | "other";

export type AgentType =
  | "module_folder_audit"
  | "assessment_compliance"
  | "moderation_compliance"
  | "attendance_compliance"
  | "evidence_verification"
  | "outcome_alignment"
  | "accreditation_readiness"
  | "programme_review";

export type AuditStatus =
  | "compliant"
  | "needs_attention"
  | "non_compliant"
  | "critical";

export type AuditRunStatus = "pending" | "running" | "completed" | "failed";

export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";

export type FindingType =
  | "missing_document"
  | "misclassified"
  | "quality_issue"
  | "recommendation"
  | "info";

export type FindingStatus =
  | "open"
  | "acknowledged"
  | "assigned"
  | "in_progress"
  | "resolution_submitted"
  | "under_review"
  | "resolved"
  | "rejected"
  | "reopened"
  | "escalated"
  | "deferred"
  | "closed";

export type UploadState =
  | "pending"
  | "scanning"
  | "ready"
  | "quarantined"
  | "failed";

export type ProcessingStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "skipped";
