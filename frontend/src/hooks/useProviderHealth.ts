"use client";

import { useQuery } from "@tanstack/react-query";
import { getProvidersHealth, getProviderStatus } from "@/lib/api/providers";

export function useProviderHealth() {
  return useQuery({
    queryKey: ["providers", "health"],
    queryFn: getProvidersHealth,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
    retry: 1,
  });
}

export function useProviderStatus() {
  return useQuery({
    queryKey: ["providers", "status"],
    queryFn: getProviderStatus,
    staleTime: 60 * 1000,
    retry: 1,
  });
}
