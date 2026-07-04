"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listComments,
  createComment,
  updateComment,
  resolveComment,
  deleteComment,
} from "@/lib/api/comments";
import { extractErrorMessage } from "@/lib/api-client";

const commentKeys = {
  audit: (id: string) => ["comments", id] as const,
};

export function useComments(auditId: string) {
  return useQuery({
    queryKey: commentKeys.audit(auditId),
    queryFn: () => listComments(auditId),
    enabled: !!auditId,
    staleTime: 30_000,
  });
}

export function useCreateComment(auditId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => createComment(auditId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: commentKeys.audit(auditId) });
      toast.success("Comment added");
    },
    onError: (err) => toast.error("Failed to add comment", { description: extractErrorMessage(err) }),
  });
}

export function useUpdateComment(auditId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) => updateComment(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: commentKeys.audit(auditId) }),
    onError: (err) => toast.error("Update failed", { description: extractErrorMessage(err) }),
  });
}

export function useResolveComment(auditId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => resolveComment(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: commentKeys.audit(auditId) }),
    onError: (err) => toast.error("Resolve failed", { description: extractErrorMessage(err) }),
  });
}

export function useDeleteComment(auditId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteComment(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: commentKeys.audit(auditId) });
      toast.success("Comment deleted");
    },
    onError: (err) => toast.error("Delete failed", { description: extractErrorMessage(err) }),
  });
}
