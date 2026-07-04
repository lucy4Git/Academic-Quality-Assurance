"use client";

import { useState } from "react";
import Link from "next/link";
import { GitBranch, Search } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatDate } from "@/lib/utils";
import { useWorkflows } from "@/hooks/useWorkflow";
import {
  WORKFLOW_STATUS_LABELS,
  WORKFLOW_STATUS_COLOURS,
  PRIORITY_LABELS,
  PRIORITY_COLOURS,
  type WorkflowStatus,
  type WorkflowItem,
} from "@/types";

const ALL_STATUSES: WorkflowStatus[] = [
  "draft", "assigned", "evidence_collection", "pending_qa_review",
  "returned_for_corrections", "approved", "rejected", "completed", "archived",
];

function WfBadge({ status }: { status: WorkflowStatus }) {
  return (
    <span className={cn(
      "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold",
      WORKFLOW_STATUS_COLOURS[status],
    )}>
      {WORKFLOW_STATUS_LABELS[status]}
    </span>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-xl" />
      ))}
    </div>
  );
}

export function WorkflowListView() {
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | "">("");
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, refetch } = useWorkflows(
    statusFilter ? { workflow_status: statusFilter } : undefined,
  );

  const filtered = (data ?? []).filter((item: WorkflowItem) =>
    item.academic_year.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow"
        subtitle="Track audit lifecycle from creation to archival"
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by year…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-background pl-8 pr-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as WorkflowStatus | "")}
          className="flex h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>{WORKFLOW_STATUS_LABELS[s]}</option>
          ))}
        </select>
      </div>

      {/* Content */}
      {isLoading && <ListSkeleton />}
      {isError && <ErrorState title="Failed to load workflow" onRetry={() => refetch()} />}
      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          title="No audits found"
          description="No audits match your filters."
          icon={GitBranch}
        />
      )}
      {!isLoading && !isError && filtered.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">Academic Year</th>
                <th className="px-4 py-3">Workflow Status</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Due Date</th>
                <th className="px-4 py-3">Compliance</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((item: WorkflowItem) => (
                <tr key={item.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3 font-medium">{item.academic_year}</td>
                  <td className="px-4 py-3">
                    <WfBadge status={item.workflow_status} />
                  </td>
                  <td className="px-4 py-3">
                    {item.priority ? (
                      <span className={cn("text-xs font-medium", PRIORITY_COLOURS[item.priority])}>
                        {PRIORITY_LABELS[item.priority]}
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {item.due_date ? formatDate(item.due_date) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      "text-xs font-semibold tabular-nums",
                      item.compliance_percentage >= 90 ? "text-green-600"
                        : item.compliance_percentage >= 70 ? "text-amber-600"
                        : "text-red-600",
                    )}>
                      {item.compliance_percentage.toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/workflow/${item.id}`}
                      className="text-xs text-primary hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
