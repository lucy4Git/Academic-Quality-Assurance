"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck, CheckCircle, XCircle, RotateCcw, FileSearch, Loader2, X,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { cn, formatDate } from "@/lib/utils";
import { useWorkflows } from "@/hooks/useWorkflow";
import { useApproveAudit, useRejectAudit, useReturnAudit, useRequestEvidence } from "@/hooks/useApprovals";
import { WORKFLOW_STATUS_COLOURS, type WorkflowItem } from "@/types";

// ---------------------------------------------------------------------------
// Remarks dialog
// ---------------------------------------------------------------------------

function RemarksDialog({
  title,
  onConfirm,
  onCancel,
  isPending,
}: {
  title: string;
  onConfirm: (remarks: string) => void;
  onCancel: () => void;
  isPending: boolean;
}) {
  const [remarks, setRemarks] = useState("");
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-xl border border-border shadow-xl w-full max-w-md p-5 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold">{title}</p>
          <button onClick={onCancel} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <textarea
          rows={4}
          placeholder="Remarks (optional but recommended)…"
          value={remarks}
          onChange={(e) => setRemarks(e.target.value)}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button size="sm" disabled={isPending} onClick={() => onConfirm(remarks)}>
            {isPending && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}
            Confirm
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Row
// ---------------------------------------------------------------------------

function ApprovalRow({ item }: { item: WorkflowItem }) {
  const approveMut = useApproveAudit();
  const rejectMut = useRejectAudit();
  const returnMut = useReturnAudit();
  const requestEvidenceMut = useRequestEvidence();

  const [dialog, setDialog] = useState<"reject" | "return" | null>(null);

  const isPending =
    approveMut.isPending ||
    rejectMut.isPending ||
    returnMut.isPending ||
    requestEvidenceMut.isPending;

  return (
    <>
      {dialog === "reject" && (
        <RemarksDialog
          title="Reject Audit"
          isPending={rejectMut.isPending}
          onCancel={() => setDialog(null)}
          onConfirm={async (remarks) => {
            await rejectMut.mutateAsync({ audit_id: item.id, remarks: remarks || null });
            setDialog(null);
          }}
        />
      )}
      {dialog === "return" && (
        <RemarksDialog
          title="Return for Corrections"
          isPending={returnMut.isPending}
          onCancel={() => setDialog(null)}
          onConfirm={async (remarks) => {
            await returnMut.mutateAsync({ audit_id: item.id, remarks: remarks || null });
            setDialog(null);
          }}
        />
      )}

      <tr className="hover:bg-muted/20 transition-colors">
        <td className="px-4 py-3">
          <Link
            href={`/workflow/${item.id}`}
            className="text-sm font-medium text-primary hover:underline"
          >
            {item.academic_year}
          </Link>
        </td>
        <td className="px-4 py-3">
          <span className={cn(
            "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold",
            WORKFLOW_STATUS_COLOURS[item.workflow_status],
          )}>
            {item.workflow_status.replace(/_/g, " ")}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className={cn(
            "text-sm font-bold tabular-nums",
            item.compliance_percentage >= 90 ? "text-green-600"
              : item.compliance_percentage >= 70 ? "text-amber-600"
              : "text-red-600",
          )}>
            {item.compliance_percentage.toFixed(0)}%
          </span>
        </td>
        <td className="px-4 py-3 text-xs text-muted-foreground">
          {item.due_date ? formatDate(item.due_date) : "—"}
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant="outline"
              className="h-7 border-green-500 text-green-700 hover:bg-green-50"
              disabled={isPending}
              onClick={() => approveMut.mutate({ audit_id: item.id })}
            >
              {approveMut.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3 mr-1" />}
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 border-orange-400 text-orange-700 hover:bg-orange-50"
              disabled={isPending}
              onClick={() => setDialog("return")}
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Return
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 border-red-400 text-red-700 hover:bg-red-50"
              disabled={isPending}
              onClick={() => setDialog("reject")}
            >
              <XCircle className="h-3 w-3 mr-1" />
              Reject
            </Button>
          </div>
        </td>
      </tr>
    </>
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function ApprovalsView() {
  const { data, isLoading, isError, refetch } = useWorkflows({
    workflow_status: "pending_qa_review",
  });

  return (
    <RoleGuard roles={["system_admin", "quality_assurance_officer"]}>
      <div className="space-y-6">
        <PageHeader
          title="Approvals"
          subtitle="Audits pending QA review"
        />

        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14 rounded-xl" />)}
          </div>
        )}

        {isError && (
          <ErrorState title="Failed to load approval queue" onRetry={() => refetch()} />
        )}

        {!isLoading && !isError && (!data || data.length === 0) && (
          <EmptyState
            title="Approval queue is empty"
            description="No audits are currently pending QA review."
            icon={FileSearch}
          />
        )}

        {!isLoading && !isError && data && data.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-border bg-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3">Academic Year</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Compliance</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.map((item: WorkflowItem) => (
                  <ApprovalRow key={item.id} item={item} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
