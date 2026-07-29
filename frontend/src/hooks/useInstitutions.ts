"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  createInstitution,
  deleteInstitution,
  getCurrentInstitution,
  getInstitution,
  getInstitutionStats,
  listInstitutions,
  updateInstitution,
} from "@/lib/api/institutions";
import { extractErrorMessage } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";
import type { InstitutionCreate, InstitutionUpdate } from "@/types";

const INSTITUTION_LIST_ROLES = new Set([
  "system_admin",
  "quality_assurance_officer",
]);

export const institutionKeys = {
  all: ["institutions"] as const,
  list: (
    userId: string,
    institutionId: string | null,
    role: string,
    includeArchived: boolean
  ) =>
    [
      ...institutionKeys.all,
      "list",
      userId,
      institutionId ?? "platform",
      role,
      { includeArchived },
    ] as const,
  current: (userId: string, institutionId: string | null) =>
    [
      ...institutionKeys.all,
      "current",
      userId,
      institutionId ?? "unassigned",
    ] as const,
  detail: (id: string) => [...institutionKeys.all, "detail", id] as const,
  stats: (id: string) => [...institutionKeys.all, "stats", id] as const,
};

/**
 * Return the institution assigned to the authenticated user.
 *
 * System administrators normally have no institution assignment, so this
 * query remains disabled for them.
 */
export function useCurrentInstitution() {
  const user = useAuthStore((state) => state.user);
  const enabled = Boolean(
    user &&
      user.role !== "system_admin" &&
      user.institution_id
  );

  return useQuery({
    queryKey: institutionKeys.current(
      user?.id ?? "anonymous",
      user?.institution_id ?? null
    ),
    queryFn: getCurrentInstitution,
    enabled,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

/**
 * Return institutions visible to the authenticated user.
 *
 * Platform/QA roles use the list endpoint. Roles that are not authorised to
 * list institutions use /institutions/current and receive a one-item array.
 * This preserves existing component contracts while preventing expected 403
 * responses for lecturers, students, deans, heads and coordinators.
 */
export function useInstitutions(includeArchived = false) {
  const user = useAuthStore((state) => state.user);
  const canListInstitutions = Boolean(
    user && INSTITUTION_LIST_ROLES.has(user.role)
  );

  return useQuery({
    queryKey: institutionKeys.list(
      user?.id ?? "anonymous",
      user?.institution_id ?? null,
      user?.role ?? "anonymous",
      includeArchived
    ),
    queryFn: async () => {
      if (canListInstitutions) {
        return listInstitutions(includeArchived);
      }

      const current = await getCurrentInstitution();
      return [current];
    },
    enabled: Boolean(user),
    staleTime: 2 * 60 * 1000,
    retry: false,
  });
}

export function useInstitution(id: string) {
  return useQuery({
    queryKey: institutionKeys.detail(id),
    queryFn: () => getInstitution(id),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  });
}

export function useInstitutionStats(id: string) {
  return useQuery({
    queryKey: institutionKeys.stats(id),
    queryFn: () => getInstitutionStats(id),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateInstitution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InstitutionCreate) => createInstitution(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: institutionKeys.all });
    },
    onError: (error) => {
      const message = extractErrorMessage(error);
      if (!message.toLowerCase().includes("already in use")) {
        toast.error("Failed to create institution", {
          description: message,
        });
      }
    },
  });
}

export function useUpdateInstitution(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InstitutionUpdate) =>
      updateInstitution(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(institutionKeys.detail(id), updated);
      queryClient.invalidateQueries({ queryKey: institutionKeys.all });
      toast.success("Institution updated");
    },
    onError: (error) => {
      toast.error("Failed to update institution", {
        description: extractErrorMessage(error),
      });
    },
  });
}

export function useDeleteInstitution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteInstitution(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: institutionKeys.all });
      toast.success("Institution deleted");
    },
    onError: (error) => {
      toast.error("Failed to delete institution", {
        description: extractErrorMessage(error),
      });
    },
  });
}
