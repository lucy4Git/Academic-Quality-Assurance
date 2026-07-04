export interface KnowledgeIndexEntry {
  institution_code: string;
  academic_year: string;
  ikp_version: string;
  collection: string;
  indexed: boolean;
  chunk_count: number | null;
}

export interface InstitutionStats {
  institution_id: string;
  institution_code: string;
  institution_name: string;
  institution_type: string;
  faculty_count: number;
  department_count: number;
  programme_count: number;
  module_count: number;
  audit_run_count: number;
  evidence_file_count: number;
  knowledge_indexed: boolean;
  qdrant_collection: string | null;
}

export interface DashboardResponse {
  institution_count: number;
  faculty_count: number;
  department_count: number;
  programme_count: number;
  module_count: number;
  audit_run_count: number;
  completed_audit_count: number;
  failed_audit_count: number;
  evidence_file_count: number;
  knowledge_index_status: KnowledgeIndexEntry[];
  by_institution: InstitutionStats[];
  generated_at: string;
  is_admin_view: boolean;
}

export interface FacultySummaryResponse {
  faculty_id: string;
  faculty_name: string;
  institution_code: string;
  department_count: number;
  programme_count: number;
  module_count: number;
}

export interface ProgrammeSummaryResponse {
  programme_id: string;
  programme_name: string;
  programme_code: string;
  nqf_level: number | null;
  faculty_name: string;
  institution_code: string;
  module_count: number;
  audit_run_count: number;
}

export interface ModuleSummaryResponse {
  module_id: string;
  module_name: string;
  module_code: string;
  academic_year: string;
  programme_name: string;
  institution_code: string;
  audit_run_count: number;
  evidence_file_count: number;
  latest_audit_status: string | null;
}

export interface ComplianceSummaryResponse {
  institution_code: string;
  total_modules: number;
  audited_modules: number;
  compliant_count: number;
  at_risk_count: number;
  non_compliant_count: number;
  unaudited_count: number;
  compliance_rate_pct: number;
}
