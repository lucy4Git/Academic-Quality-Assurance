import { apiClient } from "@/lib/api-client";
import type { WorkflowItem } from "@/types";

export interface ApprovalPayload {
  audit_id: string;
  remarks?: string | null;
}

export async function approveAudit(payload: ApprovalPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/approvals/approve", payload);
  return data;
}

export async function rejectAudit(payload: ApprovalPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/approvals/reject", payload);
  return data;
}

export async function returnAudit(payload: ApprovalPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/approvals/return", payload);
  return data;
}

export async function requestEvidence(payload: ApprovalPayload): Promise<WorkflowItem> {
  const { data } = await apiClient.post<WorkflowItem>("/approvals/request-evidence", payload);
  return data;
}
