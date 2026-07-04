"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listFaculties,
  getFaculty,
  createFaculty,
  updateFaculty,
  deleteFaculty,
} from "@/lib/api/faculties";
import { extractErrorMessage } from "@/lib/api-client";
import type { FacultyCreate, FacultyUpdate } from "@/types";

export const facultyKeys = {
  all: ["faculties"] as const,
  list: (institutionId?: string) =>
    [...facultyKeys.all, "list", institutionId ?? "all"] as const,
  detail: (id: string) => [...facultyKeys.all, "detail", id] as const,
};

export function useFaculties(institutionId?: string) {
  return useQuery({
    queryKey: facultyKeys.list(institutionId),
    queryFn: () => listFaculties(institutionId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useFaculty(id: string) {
  return useQuery({
    queryKey: facultyKeys.detail(id),
    queryFn: () => getFaculty(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateFaculty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FacultyCreate) => createFaculty(payload),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: facultyKeys.all });
      // Also invalidate institution-scoped list
      qc.invalidateQueries({
        queryKey: facultyKeys.list(created.institution_id),
      });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err);
      if (!msg.toLowerCase().includes("already in use")) {
        toast.error("Failed to create faculty", { description: msg });
      }
    },
  });
}

export function useUpdateFaculty(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FacultyUpdate) => updateFaculty(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(facultyKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: facultyKeys.all });
      toast.success("Faculty updated");
    },
    onError: (err) => {
      toast.error("Failed to update faculty", {
        description: extractErrorMessage(err),
      });
    },
  });
}

export function useDeleteFaculty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteFaculty(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: facultyKeys.all });
      toast.success("Faculty deleted");
    },
    onError: (err) => {
      toast.error("Failed to delete faculty", {
        description: extractErrorMessage(err),
      });
    },
  });
}
