import type { AuditRunStatus, AuditStatus, FindingSeverity, FindingType, FileCategory, AgentType } from "@/types/enums";

// ---------------------------------------------------------------------------
// Types (mirrors backend schemas/accreditation_readiness.py)
// ---------------------------------------------------------------------------

export interface ReadinessFindingRead {
  id: string;
  audit_run_id: string;
  finding_type: FindingType;
  severity: FindingSeverity;
  document_category: FileCategory | null;
  file_id: string | null;
  title: string;
  description: string;
  recommendation: string;
  is_resolved: boolean;
  resolved_note: string | null;
  created_at: string;
}

export interface SubAgentReadinessRead {
  group_id: string;
  label: string;
  agent_type: AgentType;
  weight: number;
  has_run: boolean;
  overall_score: number | null;
  threshold: number;
  passed: boolean;
}

export interface FindingsSummaryRead {
  total: number;
  unresolved: number;
  critical_total: number;
  critical_unresolved: number;
  high_unresolved: number;
}

export interface AccreditationReadinessReport {
  run_id: string;
  module_id: string;
  module_code: string;
  module_name: string;
  academic_year: string;
  scope_type: string;
  presence_score: number;
  quality_score: number;
  overall_score: number;
  audit_status: AuditStatus;
  risk_level: "low" | "medium" | "high" | "critical";
  total_presence_weight: number;
  achieved_presence_weight: number;
  total_quality_weight: number;
  achieved_quality_weight: number;
  evidence_completeness_percentage: number;
  sub_agent_readiness: SubAgentReadinessRead[];
  findings_summary: FindingsSummaryRead;
  gaps: string[];
  recommendations: string[];
  findings: ReadinessFindingRead[];
  finding_counts: Record<string, number>;
  summary: string;
  generated_at: string;
}

export interface AccreditationReadinessRunBrief {
  id: string;
  module_id: string;
  agent_type: AgentType;
  run_status: AuditRunStatus;
  audit_status: AuditStatus | null;
  overall_score: number | null;
  documents_present: number | null;
  documents_missing: number | null;
  triggered_by_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AccreditationReadinessRunRead {
  id: string;
  module_id: string;
  institution_id: string;
  agent_type: AgentType;
  run_status: AuditRunStatus;
  audit_status: AuditStatus | null;
  compliance_score: number | null;
  documents_present: number | null;
  documents_missing: number | null;
  total_required: number | null;
  summary: string | null;
  error_message: string | null;
  triggered_by_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  findings: ReadinessFindingRead[];
}

export interface AccreditationReadinessTriggerResponse {
  run_id: string;
  module_id: string;
  status: AuditRunStatus;
  message: string;
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

const BASE = "accreditation-readiness-audits";

export async function triggerAccreditationReadiness(
  moduleId: string,
): Promise<AccreditationReadinessTriggerResponse> {
  return apiFetch<AccreditationReadinessTriggerResponse>(
    `${BASE}/modules/${moduleId}/trigger`,
    { method: "POST" },
  );
}

export async function getLatestAccreditationReadiness(
  moduleId: string,
): Promise<AccreditationReadinessRunRead> {
  return apiFetch<AccreditationReadinessRunRead>(
    `${BASE}/modules/${moduleId}/latest`,
  );
}

export async function getAccreditationReadinessHistory(
  moduleId: string,
  params: { skip?: number; limit?: number } = {},
): Promise<AccreditationReadinessRunBrief[]> {
  const qs = new URLSearchParams();
  if (params.skip != null) qs.set("skip", String(params.skip));
  if (params.limit != null) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<AccreditationReadinessRunBrief[]>(
    `${BASE}/modules/${moduleId}/history${query ? `?${query}` : ""}`,
  );
}

export async function getAccreditationReadinessRun(
  runId: string,
): Promise<AccreditationReadinessRunRead> {
  return apiFetch<AccreditationReadinessRunRead>(`${BASE}/${runId}`);
}

export async function getAccreditationReadinessReport(
  runId: string,
): Promise<AccreditationReadinessReport> {
  return apiFetch<AccreditationReadinessReport>(`${BASE}/${runId}/report`);
}
