import { apiClient } from "@/lib/api-client";

export interface DashboardSummary {
  institutions: number;
  faculties: number;
  departments: number;
  programmes: number;
  modules: number;
  users: number;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
  return data;
}
