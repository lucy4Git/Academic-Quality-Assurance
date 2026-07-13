import type { AuditFindingRead } from "@/types/auditRun";

export interface ListFindingsParams {
  audit_run_id?: string;
  status?: string;
  severity?: string;
  finding_type?: string;
  assigned_to_id?: string;
  skip?: number;
  limit?: number;
}

export interface FindingStatusHistoryItem {
  id: string;
  finding_id: string;
  from_status: string | null;
  to_status: string;
  changed_by_id: string | null;
  note: string | null;
  created_at: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function listFindings(params: ListFindingsParams = {}): Promise<AuditFindingRead[]> {
  const qs = new URLSearchParams();
  if (params.audit_run_id) qs.set("audit_run_id", params.audit_run_id);
  if (params.status) qs.set("status", params.status);
  if (params.severity) qs.set("severity", params.severity);
  if (params.finding_type) qs.set("finding_type", params.finding_type);
  if (params.assigned_to_id) qs.set("assigned_to_id", params.assigned_to_id);
  if (params.skip != null) qs.set("skip", String(params.skip));
  if (params.limit != null) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<AuditFindingRead[]>(`findings${query ? `?${query}` : ""}`);
}

export async function getFinding(id: string): Promise<AuditFindingRead> {
  return apiFetch<AuditFindingRead>(`findings/${id}`);
}

export async function getFindingHistory(id: string): Promise<FindingStatusHistoryItem[]> {
  return apiFetch<FindingStatusHistoryItem[]>(`findings/${id}/history`);
}

export async function transitionFinding(
  id: string,
  action: string,
  note?: string,
): Promise<AuditFindingRead> {
  return apiFetch<AuditFindingRead>(`findings/${id}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to_status: action, note: note ?? null }),
  });
}

export async function assignFinding(
  id: string,
  assignee_id: string,
  due_date?: string,
): Promise<AuditFindingRead> {
  return apiFetch<AuditFindingRead>(`findings/${id}/assign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assignee_id, due_date: due_date ?? null }),
  });
}
