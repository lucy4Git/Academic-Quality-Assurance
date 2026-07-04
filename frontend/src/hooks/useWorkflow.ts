"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  assignAudit,
  updateWorkflowStatus,
  listWorkflows,
  getWorkflow,
  type AssignPayload,
  type StatusPayload,
} from "@/lib/api/workflow";
import { extractErrorMessage } from "@/lib/api-client";
import type { WorkflowStatus } from "@/types";

export const workflowKeys = {
  all: ["workflow"] as const,
  list: (p?: object) => [...workflowKeys.all, "list", p ?? {}] as const,
  detail: (id: string) => [...workflowKeys.all, "detail", id] as const,
};

export function useWorkflows(params?: {
  workflow_status?: WorkflowStatus;
  assigned_to_id?: string;
}) {
  return useQuery({
    queryKey: workflowKeys.list(params),
    queryFn: () => listWorkflows(params),
    staleTime: 30_000,
  });
}

export function useWorkflow(auditId: string) {
  return useQuery({
    queryKey: workflowKeys.detail(auditId),
    queryFn: () => getWorkflow(auditId),
    enabled: !!auditId,
    staleTime: 30_000,
  });
}

export function useAssignAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: AssignPayload) => assignAudit(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Audit assigned");
    },
    onError: (err) => toast.error("Assignment failed", { description: extractErrorMessage(err) }),
  });
}

export function useUpdateWorkflowStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: StatusPayload) => updateWorkflowStatus(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Status updated");
    },
    onError: (err) => toast.error("Update failed", { description: extractErrorMessage(err) }),
  });
}
