/**
 * TanStack Query hooks for Knowledge Search.
 */

"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  IndexRequest,
  IndexResult,
  IndexStatusResponse,
  SearchRequest,
  SearchResponse,
} from "@/types/knowledge-index";
import { apiClient, extractErrorMessage } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Index status
// ---------------------------------------------------------------------------

export function useKnowledgeIndexStatus() {
  return useQuery<IndexStatusResponse, Error>({
    queryKey: ["knowledge-index", "status"],
    queryFn: async () => {
      const res = await apiClient.get<IndexStatusResponse>("/knowledge-index/status");
      return res.data;
    },
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Trigger indexing (Admin only)
// ---------------------------------------------------------------------------

export function useTriggerIndexing() {
  return useMutation<IndexResult, Error, IndexRequest>({
    mutationFn: async (body) => {
      const res = await apiClient.post<IndexResult>("/knowledge-index/index", body);
      return res.data;
    },
  });
}

// ---------------------------------------------------------------------------
// Semantic search
// ---------------------------------------------------------------------------

export function useKnowledgeSearch() {
  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: async (body) => {
      const res = await apiClient.post<SearchResponse>("/knowledge-search", body);
      return res.data;
    },
  });
}
