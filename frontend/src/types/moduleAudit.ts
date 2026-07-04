export type ChecklistItemStatus = "compliant" | "missing" | "partial" | "not_applicable";
export type ModuleAuditStatus = "draft" | "compliant" | "at_risk" | "non_compliant";

export const CHECKLIST_ITEM_STATUS_LABELS: Record<ChecklistItemStatus, string> = {
  compliant: "Compliant",
  missing: "Missing",
  partial: "Partial",
  not_applicable: "N/A",
};

export const MODULE_AUDIT_STATUS_LABELS: Record<ModuleAuditStatus, string> = {
  draft: "Draft",
  compliant: "Compliant",
  at_risk: "At Risk",
  non_compliant: "Non-Compliant",
};

export const MODULE_AUDIT_STATUS_COLOURS: Record<ModuleAuditStatus, string> = {
  draft: "text-slate-600 bg-slate-50 border-slate-200",
  compliant: "text-green-700 bg-green-50 border-green-200",
  at_risk: "text-amber-700 bg-amber-50 border-amber-200",
  non_compliant: "text-red-700 bg-red-50 border-red-200",
};

export const CHECKLIST_ITEM_STATUS_COLOURS: Record<ChecklistItemStatus, string> = {
  compliant: "text-green-700 bg-green-50 border-green-200",
  missing: "text-red-700 bg-red-50 border-red-200",
  partial: "text-amber-700 bg-amber-50 border-amber-200",
  not_applicable: "text-slate-600 bg-slate-50 border-slate-200",
};

export interface AuditChecklistItem {
  id: string;
  audit_id: string;
  item_key: string;
  item_label: string;
  status: ChecklistItemStatus;
  comment: string | null;
  evidence_required: boolean;
  updated_at: string;
}

export interface ModuleAuditBrief {
  id: string;
  module_id: string;
  institution_id: string;
  faculty_id: string;
  department_id: string;
  programme_id: string;
  auditor_id: string | null;
  academic_year: string;
  status: ModuleAuditStatus;
  total_items: number;
  compliant_count: number;
  missing_count: number;
  partial_count: number;
  not_applicable_count: number;
  compliance_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface ModuleAudit extends ModuleAuditBrief {
  notes: string | null;
  checklist_items: AuditChecklistItem[];
}

export interface ModuleAuditCreate {
  module_id: string;
  academic_year: string;
  notes?: string | null;
}

export interface ChecklistItemUpdate {
  status: ChecklistItemStatus;
  comment?: string | null;
  evidence_required?: boolean;
}

export interface ModuleAuditUpdate {
  notes?: string | null;
  checklist?: Record<string, ChecklistItemUpdate>;
}
