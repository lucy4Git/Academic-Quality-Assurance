import { apiClient } from "@/lib/api-client";
import type { Notification } from "@/types";

export async function listNotifications(params?: {
  unread_only?: boolean;
  skip?: number;
  limit?: number;
}): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>("/notifications", { params });
  return data;
}

export async function markNotificationRead(id: string): Promise<Notification> {
  const { data } = await apiClient.patch<Notification>(`/notifications/${id}/read`, {});
  return data;
}

export async function markAllNotificationsRead(): Promise<{ updated: number }> {
  const { data } = await apiClient.patch<{ updated: number }>("/notifications/read-all", {});
  return data;
}
