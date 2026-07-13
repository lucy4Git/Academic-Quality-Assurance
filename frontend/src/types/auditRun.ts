import type { AgentType, AuditRunStatus, AuditStatus, FindingSeverity, FindingStatus, FindingType, FileCategory } from "./enums";

export type { AgentType, AuditRunStatus, AuditStatus, FindingSeverity, FindingStatus };

export const AGENT_TYPE_LABELS: Record<AgentType, string> = {
  module_folder_audit: "Module Folder Audit",
  assessment_compliance: "Assessment Compliance",
  moderation_compliance: "Moderation Compliance",
  attendance_compliance: "Attendance Compliance",
  evidence_verification: "Evidence Verification",
  outcome_alignment: "Outcome Alignment",
  accreditation_readiness: "Accreditation Readiness",
  programme_review: "Programme Review",
};

export const AUDIT_RUN_STATUS_LABELS: Record<AuditRunStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

export const AUDIT_RUN_STATUS_COLOURS: Record<AuditRunStatus, string> = {
  pending: "text-slate-600 bg-slate-50 border-slate-200",
  running: "text-blue-600 bg-blue-50 border-blue-200",
  completed: "text-green-700 bg-green-50 border-green-200",
  failed: "text-red-700 bg-red-50 border-red-200",
};

export const AUDIT_STATUS_LABELS: Record<AuditStatus, string> = {
  compliant: "Compliant",
  needs_attention: "Needs Attention",
  non_compliant: "Non-Compliant",
  critical: "Critical",
};

export const AUDIT_STATUS_COLOURS: Record<AuditStatus, string> = {
  compliant: "text-green-700 bg-green-50 border-green-200",
  needs_attention: "text-amber-700 bg-amber-50 border-amber-200",
  non_compliant: "text-red-700 bg-red-50 border-red-200",
  critical: "text-red-900 bg-red-100 border-red-300",
};

export const FINDING_SEVERITY_COLOURS: Record<FindingSeverity, string> = {
  critical: "text-red-900 bg-red-100 border-red-300",
  high: "text-red-700 bg-red-50 border-red-200",
  medium: "text-amber-700 bg-amber-50 border-amber-200",
  low: "text-blue-700 bg-blue-50 border-blue-200",
  info: "text-slate-600 bg-slate-50 border-slate-200",
};

export interface AuditRunBrief {
  id: string;
  agent_type: AgentType;
  module_id: string | null;
  programme_id: string | null;
  run_status: AuditRunStatus;
  audit_status: AuditStatus | null;
  compliance_score: number | null;
  documents_present: number | null;
  documents_missing: number | null;
  triggered_by_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export const FINDING_STATUS_LABELS: Record<FindingStatus, string> = {
  open: "Open",
  acknowledged: "Acknowledged",
  in_progress: "In Progress",
  evidence_submitted: "Evidence Submitted",
  under_review: "Under Review",
  resolved: "Resolved",
  rejected: "Rejected",
  deferred: "Deferred",
  escalated: "Escalated",
  closed_no_action: "Closed – No Action",
};

export const FINDING_STATUS_COLOURS: Record<FindingStatus, string> = {
  open: "text-slate-700 bg-slate-50 border-slate-300",
  acknowledged: "text-blue-700 bg-blue-50 border-blue-200",
  in_progress: "text-indigo-700 bg-indigo-50 border-indigo-200",
  evidence_submitted: "text-violet-700 bg-violet-50 border-violet-200",
  under_review: "text-amber-700 bg-amber-50 border-amber-200",
  resolved: "text-green-700 bg-green-50 border-green-200",
  rejected: "text-red-700 bg-red-50 border-red-200",
  deferred: "text-orange-700 bg-orange-50 border-orange-200",
  escalated: "text-rose-700 bg-rose-100 border-rose-300",
  closed_no_action: "text-slate-500 bg-slate-50 border-slate-200",
};

export interface AuditFindingRead {
  id: string;
  audit_run_id: string;
  finding_type: FindingType;
  severity: FindingSeverity;
  document_category: FileCategory | null;
  file_id: string | null;
  title: string;
  description: string;
  recommendation: string;
  status: FindingStatus;
  assigned_to_id: string | null;
  due_date: string | null;
  is_resolved: boolean;
  resolved_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditRunRead extends AuditRunBrief {
  institution_id: string;
  total_required: number | null;
  summary: string | null;
  started_at: string | null;
  error_message: string | null;
  findings: AuditFindingRead[];
}

export interface ListAuditRunsParams {
  run_status?: AuditRunStatus;
  skip?: number;
  limit?: number;
}
