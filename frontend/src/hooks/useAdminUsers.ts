"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface PendingUser {
  id: string;
  email: string;
  full_name: string;
  role_requested: string | null;
  institution_name_requested: string | null;
  reason_for_access: string | null;
  is_verified: boolean;
  approval_status: string;
  created_at: string;
}

export interface ApprovePayload {
  user_id: string;
  role: string;
  institution_id?: string | null;
}

export interface RejectPayload {
  user_id: string;
  reason?: string | null;
}

export function usePendingUsers() {
  return useQuery<PendingUser[]>({
    queryKey: ["admin-pending-users"],
    queryFn: async () => {
      const { data } = await apiClient.get<PendingUser[]>("/admin/pending-users");
      return data;
    },
  });
}

export function useAllUsers(approvalStatus?: string) {
  return useQuery<PendingUser[]>({
    queryKey: ["admin-all-users", approvalStatus],
    queryFn: async () => {
      const params = approvalStatus ? `?approval_status=${approvalStatus}` : "";
      const { data } = await apiClient.get<PendingUser[]>(`/admin/users${params}`);
      return data;
    },
  });
}

export function useApproveUser() {
  const qc = useQueryClient();
  return useMutation<PendingUser, Error, ApprovePayload>({
    mutationFn: async ({ user_id, role, institution_id }) => {
      const { data } = await apiClient.post<PendingUser>(
        `/admin/users/${user_id}/approve`,
        { role, institution_id: institution_id ?? null }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-pending-users"] });
      qc.invalidateQueries({ queryKey: ["admin-all-users"] });
    },
  });
}

export function useRejectUser() {
  const qc = useQueryClient();
  return useMutation<PendingUser, Error, RejectPayload>({
    mutationFn: async ({ user_id, reason }) => {
      const { data } = await apiClient.post<PendingUser>(
        `/admin/users/${user_id}/reject`,
        { reason: reason ?? null }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-pending-users"] });
      qc.invalidateQueries({ queryKey: ["admin-all-users"] });
    },
  });
}
