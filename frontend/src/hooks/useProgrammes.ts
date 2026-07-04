"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listProgrammes,
  getProgramme,
  createProgramme,
  updateProgramme,
  deleteProgramme,
} from "@/lib/api/programmes";
import { extractErrorMessage } from "@/lib/api-client";
import type { ProgrammeCreate, ProgrammeUpdate } from "@/types";

export const programmeKeys = {
  all: ["programmes"] as const,
  list: (departmentId?: string) =>
    [...programmeKeys.all, "list", departmentId ?? "all"] as const,
  detail: (id: string) => [...programmeKeys.all, "detail", id] as const,
};

export function useProgrammes(departmentId?: string) {
  return useQuery({
    queryKey: programmeKeys.list(departmentId),
    queryFn: () => listProgrammes(departmentId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useProgramme(id: string) {
  return useQuery({
    queryKey: programmeKeys.detail(id),
    queryFn: () => getProgramme(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateProgramme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProgrammeCreate) => createProgramme(payload),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: programmeKeys.all });
      qc.invalidateQueries({ queryKey: programmeKeys.list(created.department_id) });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err);
      if (!msg.toLowerCase().includes("already in use")) {
        toast.error("Failed to create programme", { description: msg });
      }
    },
  });
}

export function useUpdateProgramme(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProgrammeUpdate) => updateProgramme(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(programmeKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: programmeKeys.all });
      toast.success("Programme updated");
    },
    onError: (err) => {
      toast.error("Failed to update programme", {
        description: extractErrorMessage(err),
      });
    },
  });
}

export function useDeleteProgramme() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteProgramme(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: programmeKeys.all });
      toast.success("Programme deleted");
    },
    onError: (err) => {
      toast.error("Failed to delete programme", {
        description: extractErrorMessage(err),
      });
    },
  });
}
