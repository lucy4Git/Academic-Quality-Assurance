export interface AuditEvidence {
  id: string;
  institution_id: string;
  module_id: string;
  audit_id: string;
  checklist_item_id: string | null;
  uploaded_by_id: string | null;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  evidence_category: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export const EVIDENCE_CATEGORIES = [
  { value: "general",               label: "General" },
  { value: "marking_guide",         label: "Marking Guide / Rubric" },
  { value: "attendance_register",   label: "Attendance Register" },
  { value: "assessment_plan",       label: "Assessment Plan" },
  { value: "moderation_report",     label: "Moderation Report" },
  { value: "learner_evidence",      label: "Learner Evidence" },
  { value: "course_outcomes",       label: "Course Outcomes" },
  { value: "course_content",        label: "Course Content" },
  { value: "assessment_memo",       label: "Assessment Memo" },
  { value: "approval_signoff",      label: "Approval / Sign-off" },
  { value: "lecturer_evidence",     label: "Lecturer Evidence" },
] as const;

export type EvidenceCategory = (typeof EVIDENCE_CATEGORIES)[number]["value"];
