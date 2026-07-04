"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  approveAudit,
  rejectAudit,
  returnAudit,
  requestEvidence,
  type ApprovalPayload,
} from "@/lib/api/approvals";
import { extractErrorMessage } from "@/lib/api-client";
import { workflowKeys } from "./useWorkflow";

export function useApproveAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: ApprovalPayload) => approveAudit(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Audit approved");
    },
    onError: (err) => toast.error("Failed", { description: extractErrorMessage(err) }),
  });
}

export function useRejectAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: ApprovalPayload) => rejectAudit(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Audit rejected");
    },
    onError: (err) => toast.error("Failed", { description: extractErrorMessage(err) }),
  });
}

export function useReturnAudit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: ApprovalPayload) => returnAudit(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Audit returned for corrections");
    },
    onError: (err) => toast.error("Failed", { description: extractErrorMessage(err) }),
  });
}

export function useRequestEvidence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: ApprovalPayload) => requestEvidence(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: workflowKeys.all });
      toast.success("Evidence request sent");
    },
    onError: (err) => toast.error("Failed", { description: extractErrorMessage(err) }),
  });
}
