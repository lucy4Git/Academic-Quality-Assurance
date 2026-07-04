import type { UserRole, FileCategory, AgentType } from "@/types";

export const ROLE_LABELS: Record<UserRole, string> = {
  system_admin: "System Admin",
  quality_assurance_officer: "QA Officer",
  faculty_dean: "Faculty Dean",
  head_of_department: "Head of Department",
  programme_coordinator: "Programme Coordinator",
  lecturer: "Lecturer",
  student: "Student",
};

export const AGENT_LABELS: Record<AgentType, string> = {
  module_folder_audit: "Module Folder Audit",
  assessment_compliance: "Assessment Compliance",
  moderation_compliance: "Moderation Compliance",
  attendance_compliance: "Attendance Compliance",
  evidence_verification: "Evidence Verification",
  outcome_alignment: "Outcome Alignment",
  accreditation_readiness: "Accreditation Readiness",
  programme_review: "Programme Review",
};

export const FILE_CATEGORY_LABELS: Record<FileCategory, string> = {
  course_outline: "Course Outline",
  study_guide: "Study Guide",
  learning_outcomes: "Learning Outcomes",
  weekly_plan: "Weekly Plan",
  assessment_plan: "Assessment Plan",
  assessment_brief: "Assessment Brief",
  assessment_rubric: "Assessment Rubric",
  assessment_memo: "Assessment Memo",
  exam_paper: "Exam Paper",
  practical_task: "Practical Task",
  marked_sample: "Marked Sample",
  mark_sheet: "Mark Sheet",
  internal_moderation: "Internal Moderation",
  external_moderation: "External Moderation",
  moderation_evidence: "Moderation Evidence",
  attendance_register: "Attendance Register",
  tutorial_attendance: "Tutorial Attendance",
  practical_attendance: "Practical Attendance",
  lms_participation: "LMS Participation",
  student_feedback: "Student Feedback",
  accreditation_evidence: "Accreditation Evidence",
  other: "Other",
};

/** Grouped file categories for the Upload category selector */
export const FILE_CATEGORY_GROUPS: { label: string; categories: FileCategory[] }[] = [
  {
    label: "Course Materials",
    categories: ["course_outline", "study_guide", "learning_outcomes", "weekly_plan"],
  },
  {
    label: "Assessment",
    categories: [
      "assessment_plan",
      "assessment_brief",
      "assessment_rubric",
      "assessment_memo",
      "exam_paper",
      "practical_task",
    ],
  },
  {
    label: "Moderation",
    categories: ["internal_moderation", "external_moderation", "moderation_evidence"],
  },
  {
    label: "Marked Work",
    categories: ["marked_sample", "mark_sheet"],
  },
  {
    label: "Attendance",
    categories: [
      "attendance_register",
      "tutorial_attendance",
      "practical_attendance",
      "lms_participation",
    ],
  },
  {
    label: "Feedback",
    categories: ["student_feedback"],
  },
  {
    label: "Accreditation",
    categories: ["accreditation_evidence"],
  },
  {
    label: "Other",
    categories: ["other"],
  },
];

/** Roles that can trigger audits */
export const AUDIT_TRIGGER_ROLES: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
];

/** Roles that can upload evidence */
export const UPLOAD_ROLES: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
  "lecturer",
];

/** Roles that can resolve findings */
export const RESOLVE_ROLES: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
  "lecturer",
];

/** All 7 module-scoped audit agents */
export const MODULE_AGENTS: AgentType[] = [
  "module_folder_audit",
  "assessment_compliance",
  "moderation_compliance",
  "attendance_compliance",
  "evidence_verification",
  "outcome_alignment",
  "accreditation_readiness",
];

/** Agent → API route prefix */
export const AGENT_ROUTE_PREFIX: Record<AgentType, string> = {
  module_folder_audit: "/audits",
  assessment_compliance: "/assessment-audits",
  moderation_compliance: "/moderation-audits",
  attendance_compliance: "/attendance-audits",
  evidence_verification: "/evidence-audits",
  outcome_alignment: "/outcome-alignment-audits",
  accreditation_readiness: "/accreditation-readiness-audits",
  programme_review: "/programme-review-audits",
};
