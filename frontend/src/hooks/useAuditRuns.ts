"use client";

import { useQuery } from "@tanstack/react-query";
import { listAuditRuns, getAuditRun } from "@/lib/api/auditRuns";
import type { ListAuditRunsParams } from "@/types/auditRun";

export const auditRunKeys = {
  all: ["auditRuns"] as const,
  list: (params?: ListAuditRunsParams) => [...auditRunKeys.all, "list", params ?? {}] as const,
  detail: (id: string) => [...auditRunKeys.all, "detail", id] as const,
};

export function useAuditRuns(params?: ListAuditRunsParams) {
  return useQuery({
    queryKey: auditRunKeys.list(params),
    queryFn: () => listAuditRuns(params),
    staleTime: 30 * 1000,
  });
}

export function useAuditRun(id: string) {
  return useQuery({
    queryKey: auditRunKeys.detail(id),
    queryFn: () => getAuditRun(id),
    enabled: !!id,
    staleTime: 30 * 1000,
  });
}
