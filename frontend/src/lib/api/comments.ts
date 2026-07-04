import { apiClient } from "@/lib/api-client";
import type { AuditComment } from "@/types";

export async function listComments(auditId: string): Promise<AuditComment[]> {
  const { data } = await apiClient.get<AuditComment[]>(`/comments/${auditId}`);
  return data;
}

export async function createComment(auditId: string, body: string): Promise<AuditComment> {
  const { data } = await apiClient.post<AuditComment>("/comments", { audit_id: auditId, body });
  return data;
}

export async function updateComment(commentId: string, body: string): Promise<AuditComment> {
  const { data } = await apiClient.patch<AuditComment>(`/comments/${commentId}`, { body });
  return data;
}

export async function resolveComment(commentId: string): Promise<AuditComment> {
  const { data } = await apiClient.patch<AuditComment>(`/comments/${commentId}/resolve`, {});
  return data;
}

export async function deleteComment(commentId: string): Promise<void> {
  await apiClient.delete(`/comments/${commentId}`);
}
