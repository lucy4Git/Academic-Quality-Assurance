import { apiClient } from "@/lib/api-client";
import type { AuditEvidence, AuditHistory } from "@/types";

export interface ListEvidenceParams {
  audit_id?: string;
  checklist_item_id?: string;
  module_id?: string;
}

export async function listEvidence(params?: ListEvidenceParams): Promise<AuditEvidence[]> {
  const { data } = await apiClient.get<AuditEvidence[]>("/evidence", { params });
  return data;
}

export async function listAuditEvidence(auditId: string): Promise<AuditEvidence[]> {
  const { data } = await apiClient.get<AuditEvidence[]>(`/audits/${auditId}/evidence`);
  return data;
}

export async function listItemEvidence(itemId: string): Promise<AuditEvidence[]> {
  const { data } = await apiClient.get<AuditEvidence[]>(`/checklist-items/${itemId}/evidence`);
  return data;
}

export async function getEvidence(id: string): Promise<AuditEvidence> {
  const { data } = await apiClient.get<AuditEvidence>(`/evidence/${id}`);
  return data;
}

export async function uploadEvidence(
  file: File,
  auditId: string,
  checklistItemId?: string | null,
  evidenceCategory?: string,
  description?: string | null,
): Promise<AuditEvidence> {
  const form = new FormData();
  form.append("file", file);
  form.append("audit_id", auditId);
  if (checklistItemId) form.append("checklist_item_id", checklistItemId);
  if (evidenceCategory) form.append("evidence_category", evidenceCategory);
  if (description) form.append("description", description);

  const { data } = await apiClient.post<AuditEvidence>("/evidence/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteEvidence(id: string): Promise<void> {
  await apiClient.delete(`/evidence/${id}`);
}

/** Return a proxy URL that the browser can use to download the file (cookie-authenticated). */
export function evidenceDownloadUrl(id: string): string {
  return `/api/proxy/evidence/${id}/download`;
}

/** Return a proxy URL for inline preview (PDF, image, text). */
export function evidencePreviewUrl(id: string): string {
  return `/api/proxy/evidence/${id}/preview`;
}

export async function listAuditHistory(auditId: string): Promise<AuditHistory[]> {
  const { data } = await apiClient.get<AuditHistory[]>(`/audits/${auditId}/history`);
  return data;
}
