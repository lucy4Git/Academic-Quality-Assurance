"use client";

import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { getMe } from "@/lib/api/auth";

/**
 * Primary auth hook. Fetches /auth/me on mount to rehydrate the session,
 * then exposes the user object and auth state from the Zustand store.
 */
export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, clearUser } =
    useAuthStore();

  // Rehydrate session by fetching the current user from the API.
  // Runs once on mount; the Next.js proxy forwards the httpOnly cookie as
  // a Bearer header to the FastAPI backend.
  useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        const me = await getMe();
        setUser(me);
        return me;
      } catch {
        clearUser();
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    retry: false,
  });

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      clearUser();
      // Hard navigation clears TanStack Query cache and ensures the
      // browser sends no stale cookies on the next request — same
      // approach used in the login success handler.
      window.location.href = "/login";
    }
  }, [clearUser]);

  return {
    user,
    isAuthenticated,
    isLoading,
    logout,
  };
}
