import { apiClient } from "@/lib/api-client";
import type { User } from "@/types";

/** Fetch the current authenticated user's profile */
export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
