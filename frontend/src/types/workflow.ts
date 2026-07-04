export type WorkflowStatus =
  | "draft"
  | "assigned"
  | "evidence_collection"
  | "pending_qa_review"
  | "returned_for_corrections"
  | "approved"
  | "rejected"
  | "completed"
  | "archived";

export type AuditPriority = "low" | "medium" | "high" | "critical";

export interface WorkflowItem {
  id: string;
  module_id: string;
  institution_id: string;
  academic_year: string;
  workflow_status: WorkflowStatus;
  status: string;
  compliance_percentage: number;
  assigned_to_id: string | null;
  assigned_by_id: string | null;
  assigned_date: string | null;
  due_date: string | null;
  priority: AuditPriority | null;
  assignment_remarks: string | null;
  created_at: string;
  updated_at: string;
}

export const WORKFLOW_STATUS_LABELS: Record<WorkflowStatus, string> = {
  draft: "Draft",
  assigned: "Assigned",
  evidence_collection: "Evidence Collection",
  pending_qa_review: "Pending QA Review",
  returned_for_corrections: "Returned for Corrections",
  approved: "Approved",
  rejected: "Rejected",
  completed: "Completed",
  archived: "Archived",
};

export const WORKFLOW_STATUS_COLOURS: Record<WorkflowStatus, string> = {
  draft: "border-slate-300 bg-slate-50 text-slate-700",
  assigned: "border-blue-300 bg-blue-50 text-blue-700",
  evidence_collection: "border-indigo-300 bg-indigo-50 text-indigo-700",
  pending_qa_review: "border-amber-300 bg-amber-50 text-amber-700",
  returned_for_corrections: "border-orange-300 bg-orange-50 text-orange-700",
  approved: "border-green-300 bg-green-50 text-green-700",
  rejected: "border-red-300 bg-red-50 text-red-700",
  completed: "border-emerald-300 bg-emerald-50 text-emerald-700",
  archived: "border-gray-300 bg-gray-50 text-gray-500",
};

export const PRIORITY_LABELS: Record<AuditPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export const PRIORITY_COLOURS: Record<AuditPriority, string> = {
  low: "text-slate-500",
  medium: "text-amber-600",
  high: "text-orange-600",
  critical: "text-red-600",
};
