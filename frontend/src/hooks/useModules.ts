"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listModules,
  getModule,
  createModule,
  updateModule,
  deleteModule,
  type ListModulesParams,
} from "@/lib/api/modules";
import { extractErrorMessage } from "@/lib/api-client";
import type { ModuleCreate, ModuleUpdate } from "@/types";

export const moduleKeys = {
  all: ["modules"] as const,
  list: (params?: ListModulesParams) =>
    [...moduleKeys.all, "list", params ?? {}] as const,
  detail: (id: string) => [...moduleKeys.all, "detail", id] as const,
};

export function useModules(params?: ListModulesParams) {
  return useQuery({
    queryKey: moduleKeys.list(params),
    queryFn: () => listModules(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useModule(id: string) {
  return useQuery({
    queryKey: moduleKeys.detail(id),
    queryFn: () => getModule(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateModule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ModuleCreate) => createModule(payload),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: moduleKeys.all });
      qc.invalidateQueries({
        queryKey: moduleKeys.list({ programme_id: created.programme_id }),
      });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err);
      if (!msg.toLowerCase().includes("already in use")) {
        toast.error("Failed to create module", { description: msg });
      }
    },
  });
}

export function useUpdateModule(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ModuleUpdate) => updateModule(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(moduleKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: moduleKeys.all });
      toast.success("Module updated");
    },
    onError: (err) => {
      toast.error("Failed to update module", {
        description: extractErrorMessage(err),
      });
    },
  });
}

export function useDeleteModule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteModule(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: moduleKeys.all });
      toast.success("Module deleted");
    },
    onError: (err) => {
      toast.error("Failed to delete module", {
        description: extractErrorMessage(err),
      });
    },
  });
}
