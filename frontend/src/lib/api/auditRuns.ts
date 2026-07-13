import { apiClient } from "@/lib/api-client";
import type { AuditRunBrief, AuditRunRead, ListAuditRunsParams } from "@/types/auditRun";

export async function listAuditRuns(params?: ListAuditRunsParams): Promise<AuditRunBrief[]> {
  const { data } = await apiClient.get<AuditRunBrief[]>("/audits", { params });
  return data;
}

export async function getAuditRun(id: string): Promise<AuditRunRead> {
  const { data } = await apiClient.get<AuditRunRead>(`/audits/${id}`);
  return data;
}
