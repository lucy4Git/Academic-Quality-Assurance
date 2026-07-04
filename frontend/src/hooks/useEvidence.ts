"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listEvidence,
  listAuditEvidence,
  listItemEvidence,
  getEvidence,
  uploadEvidence,
  deleteEvidence,
  listAuditHistory,
  type ListEvidenceParams,
} from "@/lib/api/evidence";
import { extractErrorMessage } from "@/lib/api-client";

export const evidenceKeys = {
  all: ["evidence"] as const,
  list: (p?: ListEvidenceParams) => [...evidenceKeys.all, "list", p ?? {}] as const,
  audit: (id: string) => [...evidenceKeys.all, "audit", id] as const,
  item: (id: string) => [...evidenceKeys.all, "item", id] as const,
  detail: (id: string) => [...evidenceKeys.all, "detail", id] as const,
  history: (id: string) => ["audit-history", id] as const,
};

export function useEvidence(params?: ListEvidenceParams) {
  return useQuery({
    queryKey: evidenceKeys.list(params),
    queryFn: () => listEvidence(params),
    staleTime: 60 * 1000,
  });
}

export function useAuditEvidence(auditId: string) {
  return useQuery({
    queryKey: evidenceKeys.audit(auditId),
    queryFn: () => listAuditEvidence(auditId),
    enabled: !!auditId,
    staleTime: 60 * 1000,
  });
}

export function useItemEvidence(itemId: string) {
  return useQuery({
    queryKey: evidenceKeys.item(itemId),
    queryFn: () => listItemEvidence(itemId),
    enabled: !!itemId,
    staleTime: 60 * 1000,
  });
}

export function useUploadEvidence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      auditId,
      checklistItemId,
      evidenceCategory,
      description,
    }: {
      file: File;
      auditId: string;
      checklistItemId?: string | null;
      evidenceCategory?: string;
      description?: string | null;
    }) => uploadEvidence(file, auditId, checklistItemId, evidenceCategory, description),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: evidenceKeys.all });
      toast.success("Evidence uploaded");
    },
    onError: (err) =>
      toast.error("Upload failed", { description: extractErrorMessage(err) }),
  });
}

export function useAuditHistory(auditId: string) {
  return useQuery({
    queryKey: evidenceKeys.history(auditId),
    queryFn: () => listAuditHistory(auditId),
    enabled: !!auditId,
    staleTime: 30 * 1000,
  });
}

export function useDeleteEvidence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteEvidence(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: evidenceKeys.all });
      toast.success("Evidence deleted");
    },
    onError: (err) =>
      toast.error("Delete failed", { description: extractErrorMessage(err) }),
  });
}
