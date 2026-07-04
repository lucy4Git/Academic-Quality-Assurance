"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listDepartments,
  getDepartment,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from "@/lib/api/departments";
import { extractErrorMessage } from "@/lib/api-client";
import type { DepartmentCreate, DepartmentUpdate } from "@/types";

export const departmentKeys = {
  all: ["departments"] as const,
  list: (facultyId?: string) =>
    [...departmentKeys.all, "list", facultyId ?? "all"] as const,
  detail: (id: string) => [...departmentKeys.all, "detail", id] as const,
};

export function useDepartments(facultyId?: string) {
  return useQuery({
    queryKey: departmentKeys.list(facultyId),
    queryFn: () => listDepartments(facultyId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useDepartment(id: string) {
  return useQuery({
    queryKey: departmentKeys.detail(id),
    queryFn: () => getDepartment(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DepartmentCreate) => createDepartment(payload),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: departmentKeys.all });
      qc.invalidateQueries({ queryKey: departmentKeys.list(created.faculty_id) });
    },
    onError: (err) => {
      const msg = extractErrorMessage(err);
      if (!msg.toLowerCase().includes("already in use")) {
        toast.error("Failed to create department", { description: msg });
      }
    },
  });
}

export function useUpdateDepartment(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DepartmentUpdate) => updateDepartment(id, payload),
    onSuccess: (updated) => {
      qc.setQueryData(departmentKeys.detail(id), updated);
      qc.invalidateQueries({ queryKey: departmentKeys.all });
      toast.success("Department updated");
    },
    onError: (err) => {
      toast.error("Failed to update department", {
        description: extractErrorMessage(err),
      });
    },
  });
}

export function useDeleteDepartment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDepartment(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: departmentKeys.all });
      toast.success("Department deleted");
    },
    onError: (err) => {
      toast.error("Failed to delete department", {
        description: extractErrorMessage(err),
      });
    },
  });
}
