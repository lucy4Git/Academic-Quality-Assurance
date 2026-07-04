"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  IkpChunkPage,
  IkpCreateReviewBatchRequest,
  IkpCreateReviewBatchResult,
  IkpPackageSummary,
  IkpReindexRequest,
  IkpReindexResult,
} from "@/types/ikp";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const ikpKeys = {
  all: ["ikp"] as const,
  packages: (institutionCode?: string) =>
    ["ikp", "packages", institutionCode ?? "all"] as const,
  package: (code: string, year: string, version: string) =>
    ["ikp", "packages", code, year, version] as const,
  chunks: (code: string, year: string, version: string, entityType?: string, skip?: number) =>
    ["ikp", "chunks", code, year, version, entityType ?? "all", skip ?? 0] as const,
};

// ---------------------------------------------------------------------------
// List packages
// ---------------------------------------------------------------------------

export function useIkpPackages(institutionCode?: string) {
  return useQuery<IkpPackageSummary[]>({
    queryKey: ikpKeys.packages(institutionCode),
    queryFn: async () => {
      const res = await apiClient.get("/ikp/packages");
      return res.data as IkpPackageSummary[];
    },
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Package detail
// ---------------------------------------------------------------------------

export function useIkpPackage(code: string, year: string, version: string) {
  return useQuery<IkpPackageSummary>({
    queryKey: ikpKeys.package(code, year, version),
    queryFn: async () => {
      const res = await apiClient.get(`/ikp/packages/${code}/${year}/${version}`);
      return res.data as IkpPackageSummary;
    },
    enabled: Boolean(code && year && version),
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Chunks (paginated)
// ---------------------------------------------------------------------------

export function useIkpChunks(
  code: string,
  year: string,
  version: string,
  options: { entityType?: string; skip?: number; limit?: number; enabled?: boolean }
) {
  const { entityType, skip = 0, limit = 50, enabled = true } = options;
  return useQuery<IkpChunkPage>({
    queryKey: ikpKeys.chunks(code, year, version, entityType, skip),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (entityType) params.set("entity_type", entityType);
      params.set("skip", String(skip));
      params.set("limit", String(limit));
      const res = await apiClient.get(
        `/ikp/packages/${code}/${year}/${version}/chunks?${params.toString()}`
      );
      return res.data as IkpChunkPage;
    },
    enabled: Boolean(code && year && version) && enabled,
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Re-index mutation
// ---------------------------------------------------------------------------

export function useIkpReindex(code: string, year: string, version: string) {
  const queryClient = useQueryClient();
  return useMutation<IkpReindexResult, Error, IkpReindexRequest>({
    mutationFn: async (body) => {
      const res = await apiClient.post(
        `/ikp/packages/${code}/${year}/${version}/reindex`,
        body
      );
      return res.data as IkpReindexResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ikpKeys.all });
    },
  });
}

// ---------------------------------------------------------------------------
// Create review batch mutation
// ---------------------------------------------------------------------------

export function useIkpCreateReviewBatch(code: string, year: string, version: string) {
  return useMutation<IkpCreateReviewBatchResult, Error, IkpCreateReviewBatchRequest>({
    mutationFn: async (body) => {
      const res = await apiClient.post(
        `/ikp/packages/${code}/${year}/${version}/create-review-batch`,
        body
      );
      return res.data as IkpCreateReviewBatchResult;
    },
  });
}
