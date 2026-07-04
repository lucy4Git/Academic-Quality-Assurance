"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listInstitutions,
  getInstitution,
  getInstitutionStats,
  createInstitution,
  updateInstitution,
  deleteInstitution,
} from "@/lib/api/institutions";
import { extractErrorMessage } from "@/lib/api-client";
import type { InstitutionCreate, InstitutionUpdate } from "@/types";

export const institutionKeys = {
  all: ["institutions"] as const,
  list: () => [...institutionKeys.all, "list"] as const,
  detail: (id: string) => [...institutionKeys.all, "detail", id] as const,
  stats: (id: string) => [...institutionKeys.all, "stats", id] as const,
};

export function useInstitutions(includeArchived = false) {
  return useQuery({
    queryKey: [...institutionKeys.list(), { includeArchived }],
    queryFn: () => listInstitutions(includeArchived),
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitution(id: string) {
  return useQuery({
    queryKey: institutionKeys.detail(id),
    queryFn: () => getInstitution(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitutionStats(id: string) {
  return useQuery({
    queryKey: institutionKeys.stats(id),
    queryFn: () => getInstitutionStats(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateInstitution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionCreate) => createInstitution(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: institutionKeys.list() });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err);
      if (!msg.toLowerCase().includes("already in use")) {
        toast.error("Failed to create institution", { description: msg });
      }
    },
  });
}

export function useUpdateInstitution(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionUpdate) => updateInstitution(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(institutionKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: institutionKeys.list() });
      toast.success("Institution updated");
    },
    onError: (err) => {
      toast.error("Failed to update institution", {
        description: extractErrorMessage(err),
      });
    },
  });
}

export function useDeleteInstitution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteInstitution(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: institutionKeys.list() });
      toast.success("Institution deleted");
    },
    onError: (err) => {
      toast.error("Failed to delete institution", {
        description: extractErrorMessage(err),
      });
    },
  });
}
