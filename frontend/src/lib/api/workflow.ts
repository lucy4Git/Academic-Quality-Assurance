import { apiClient } from "@/lib/api-client";
import type { WorkflowItem, WorkflowStatus, AuditPriority } from "@/types";

export interface AssignPayload {
  audit_id: string;
  assigned_to_id: string;
  due_date?: string | null;
  priority?: AuditPriority | null;
  remarks?: string | null;
}

export interface StatusPayload {
  audit_id: string;
  new_status: WorkflowStatus;
  remarks?: string | null;
}

export async function assignAudit(payload: AssignPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/workflow/assign", payload);
  return data;
}

export async function updateWorkflowStatus(payload: StatusPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/workflow/status", payload);
  return data;
}

export async function listWorkflows(params?: {
  workflow_status?: WorkflowStatus;
  assigned_to_id?: string;
  skip?: number;
  limit?: number;
}): Promise<WorkflowItem[]> {
  const { data } = await apiClient.get<WorkflowItem[]>("/workflow", { params });
  return data;
}

export async function getWorkflow(auditId: string): Promise<WorkflowItem> {
  const { data } = await apiClient.get<WorkflowItem>(`/workflow/${auditId}`);
  return data;
}
