/**
 * TanStack Query hooks for the Knowledge Review Centre.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ApproveAllEligibleResult,
  ApproveItemRequest,
  BatchFromADIPRequest,
  EditItemRequest,
  ExportResult,
  KnowledgeReviewBatch,
  KnowledgeReviewBatchSummary,
  KnowledgeReviewItem,
  RejectItemRequest,
} from "@/types/knowledge-review";

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Batch hooks
// ---------------------------------------------------------------------------

export function useKnowledgeReviewBatches(params?: {
  skip?: number;
  limit?: number;
}) {
  const skip = params?.skip ?? 0;
  const limit = params?.limit ?? 50;
  return useQuery<KnowledgeReviewBatchSummary[]>({
    queryKey: ["knowledge-review", "batches", skip, limit],
    queryFn: () =>
      apiFetch<KnowledgeReviewBatchSummary[]>(
        `knowledge-review/batches?skip=${skip}&limit=${limit}`
      ),
  });
}

export function useKnowledgeReviewBatch(batchId: string | undefined) {
  return useQuery<KnowledgeReviewBatch>({
    queryKey: ["knowledge-review", "batch", batchId],
    queryFn: () =>
      apiFetch<KnowledgeReviewBatch>(`knowledge-review/batches/${batchId}`),
    enabled: !!batchId,
  });
}

export function useCreateBatchFromADIP() {
  const queryClient = useQueryClient();
  return useMutation<KnowledgeReviewBatch, Error, BatchFromADIPRequest>({
    mutationFn: (data) =>
      apiFetch<KnowledgeReviewBatch>(
        "knowledge-review/batches/from-adip-output",
        { method: "POST", body: JSON.stringify(data) }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batches"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Item hooks
// ---------------------------------------------------------------------------

export function useKnowledgeReviewItems(params: {
  batchId: string;
  entityType?: string;
  status?: string;
  skip?: number;
  limit?: number;
}) {
  const { batchId, entityType, status, skip = 0, limit = 100 } = params;
  const searchParams = new URLSearchParams({ batch_id: batchId });
  if (entityType) searchParams.set("entity_type", entityType);
  if (status) searchParams.set("status", status);
  searchParams.set("skip", String(skip));
  searchParams.set("limit", String(limit));

  return useQuery<KnowledgeReviewItem[]>({
    queryKey: ["knowledge-review", "items", batchId, entityType, status, skip, limit],
    queryFn: () =>
      apiFetch<KnowledgeReviewItem[]>(
        `knowledge-review/items?${searchParams.toString()}`
      ),
    enabled: !!batchId,
  });
}

export function useKnowledgeReviewItem(itemId: string | undefined) {
  return useQuery<KnowledgeReviewItem>({
    queryKey: ["knowledge-review", "item", itemId],
    queryFn: () =>
      apiFetch<KnowledgeReviewItem>(`knowledge-review/items/${itemId}`),
    enabled: !!itemId,
  });
}

// ---------------------------------------------------------------------------
// Item action mutations
// ---------------------------------------------------------------------------

function useItemActionMutation(batchId: string) {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["knowledge-review", "items", batchId] });
    queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
  };
  return invalidate;
}

export function useApproveItem(batchId: string) {
  const queryClient = useQueryClient();
  return useMutation<KnowledgeReviewItem, Error, { itemId: string; body: ApproveItemRequest }>({
    mutationFn: ({ itemId, body }) =>
      apiFetch<KnowledgeReviewItem>(`knowledge-review/items/${itemId}/approve`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "items", batchId] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
    },
  });
}

export function useRejectItem(batchId: string) {
  const queryClient = useQueryClient();
  return useMutation<KnowledgeReviewItem, Error, { itemId: string; body: RejectItemRequest }>({
    mutationFn: ({ itemId, body }) =>
      apiFetch<KnowledgeReviewItem>(`knowledge-review/items/${itemId}/reject`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "items", batchId] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
    },
  });
}

export function useEditItem(batchId: string) {
  const queryClient = useQueryClient();
  return useMutation<KnowledgeReviewItem, Error, { itemId: string; body: EditItemRequest }>({
    mutationFn: ({ itemId, body }) =>
      apiFetch<KnowledgeReviewItem>(`knowledge-review/items/${itemId}/edit`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "items", batchId] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Batch bulk action mutations
// ---------------------------------------------------------------------------

export function useApproveAllEligible(batchId: string) {
  const queryClient = useQueryClient();
  return useMutation<ApproveAllEligibleResult, Error, void>({
    mutationFn: () =>
      apiFetch<ApproveAllEligibleResult>(
        `knowledge-review/batches/${batchId}/approve-all-eligible`,
        { method: "POST" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "items", batchId] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
    },
  });
}

export function useExportApprovedIKP(batchId: string) {
  const queryClient = useQueryClient();
  return useMutation<ExportResult, Error, void>({
    mutationFn: () =>
      apiFetch<ExportResult>(
        `knowledge-review/batches/${batchId}/export-approved-ikp`,
        { method: "POST" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batch", batchId] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-review", "batches"] });
    },
  });
}
