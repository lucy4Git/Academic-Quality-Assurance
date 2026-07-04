"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listAudits,
  listModuleAudits,
  getAudit,
  createAudit,
  updateAudit,
  deleteAudit,
  type ListAuditsParams,
} from "@/lib/api/moduleAudits";
import { extractErrorMessage } from "@/lib/api-client";
import type { ModuleAuditCreate, ModuleAuditUpdate } from "@/types";

export const auditKeys = {
  all: ["audits"] as const,
  list: (params?: ListAuditsParams) => [...auditKeys.all, "list", params ?? {}] as const,
  moduleList: (moduleId: string) => [...auditKeys.all, "module", moduleId] as const,
  detail: (id: string) => [...auditKeys.all, "detail", id] as const,
};

export function useAudits(params?: ListAuditsParams) {
  return useQuery({
    queryKey: auditKeys.list(params),
    queryFn: () => listAudits(params),
    staleTime: 60 * 1000,
  });
}

export function useModuleAuditsList(moduleId: string) {
  return useQuery({
    queryKey: auditKeys.moduleList(moduleId),
    queryFn: () => listModuleAudits(moduleId),
    enabled: !!moduleId,
    staleTime: 60 * 1000,
  });
}

export function useAudit(id: string) {
  return useQuery({
    queryKey: auditKeys.detail(id),
    queryFn: () => getAudit(id),
    enabled: !!id,
    staleTime: 30 * 1000,
  });
}

export function useCreateAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ModuleAuditCreate) => createAudit(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: auditKeys.all }),
    onError: (err) =>
      toast.error("Failed to create audit", { description: extractErrorMessage(err) }),
  });
}

export function useUpdateAudit(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ModuleAuditUpdate) => updateAudit(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(auditKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: auditKeys.all });
      toast.success("Audit updated");
    },
    onError: (err) =>
      toast.error("Failed to update audit", { description: extractErrorMessage(err) }),
  });
}

export function useDeleteAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAudit(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: auditKeys.all });
      toast.success("Audit deleted");
    },
    onError: (err) =>
      toast.error("Failed to delete audit", { description: extractErrorMessage(err) }),
  });
}
