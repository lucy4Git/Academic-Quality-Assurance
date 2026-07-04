import { apiClient } from "@/lib/api-client";
import type {
  ModuleAudit,
  ModuleAuditBrief,
  ModuleAuditCreate,
  ModuleAuditStatus,
  ModuleAuditUpdate,
} from "@/types";

export interface ListAuditsParams {
  module_id?: string;
  institution_id?: string;
  status?: ModuleAuditStatus;
  skip?: number;
  limit?: number;
}

export async function listAudits(params?: ListAuditsParams): Promise<ModuleAuditBrief[]> {
  const { data } = await apiClient.get<ModuleAuditBrief[]>("/audits", { params });
  return data;
}

export async function listModuleAudits(moduleId: string): Promise<ModuleAuditBrief[]> {
  const { data } = await apiClient.get<ModuleAuditBrief[]>(`/modules/${moduleId}/audits`);
  return data;
}

export async function getAudit(id: string): Promise<ModuleAudit> {
  const { data } = await apiClient.get<ModuleAudit>(`/audits/${id}`);
  return data;
}

export async function createAudit(payload: ModuleAuditCreate): Promise<ModuleAudit> {
  const { data } = await apiClient.post<ModuleAudit>("/audits", payload);
  return data;
}

export async function updateAudit(id: string, payload: ModuleAuditUpdate): Promise<ModuleAudit> {
  const { data } = await apiClient.patch<ModuleAudit>(`/audits/${id}`, payload);
  return data;
}

export async function deleteAudit(id: string): Promise<void> {
  await apiClient.delete(`/audits/${id}`);
}
