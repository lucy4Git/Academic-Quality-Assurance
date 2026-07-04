"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/lib/api/notifications";
import { extractErrorMessage } from "@/lib/api-client";

export const notifKeys = {
  all: ["notifications"] as const,
  list: (p?: object) => [...notifKeys.all, "list", p ?? {}] as const,
};

export function useNotifications(params?: { unread_only?: boolean }) {
  return useQuery({
    queryKey: notifKeys.list(params),
    queryFn: () => listNotifications(params),
    staleTime: 15_000,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: notifKeys.all }),
    onError: (err) => toast.error("Error", { description: extractErrorMessage(err) }),
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: notifKeys.all });
      toast.success(`Marked ${data.updated} notification${data.updated !== 1 ? "s" : ""} as read`);
    },
    onError: (err) => toast.error("Error", { description: extractErrorMessage(err) }),
  });
}
