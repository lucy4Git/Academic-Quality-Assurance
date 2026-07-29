"use client";

import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { getMe } from "@/lib/api/auth";

/**
 * Primary auth hook. Fetches /auth/me on mount to rehydrate the session,
 * then exposes the user object and auth state from the Zustand store.
 */
export function useAuth() {
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading, setUser, clearUser } =
    useAuthStore();

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
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      await queryClient.cancelQueries();

      // Remove all user-, institution-, conversation- and workspace-scoped
      // data before another account can sign in within the same browser tab.
      queryClient.clear();
      clearUser();

      if (typeof window !== "undefined") {
        useAuthStore.persist.clearStorage();
        window.sessionStorage.removeItem("aqaa-auth");
      }

      window.location.replace("/login");
    }
  }, [clearUser, queryClient]);

  return {
    user,
    isAuthenticated,
    isLoading,
    logout,
  };
}
