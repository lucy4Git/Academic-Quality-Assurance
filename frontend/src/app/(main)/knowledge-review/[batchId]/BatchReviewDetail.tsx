"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfidenceBadge } from "@/components/knowledge-review/ConfidenceBadge";
import { ReviewStatusBadge } from "@/components/knowledge-review/ReviewStatusBadge";
import { EditValueDialog } from "@/components/knowledge-review/EditValueDialog";
import {
  useKnowledgeReviewBatch,
  useKnowledgeReviewItems,
  useApproveItem,
  useRejectItem,
  useEditItem,
  useApproveAllEligible,
  useExportApprovedIKP,
} from "@/hooks/useKnowledgeReview";
import type { KnowledgeReviewItem } from "@/types/knowledge-review";

interface BatchReviewDetailProps {
  batchId: string;
}

type EntityTypeFilter = "all" | "programme" | "module" | "admission_requirement";
type StatusFilter = "all" | "pending_review" | "approved" | "rejected" | "edited";
type ConfidenceFilter = "all" | "high" | "medium";

export function BatchReviewDetail({ batchId }: BatchReviewDetailProps) {
  const [entityTypeFilter, setEntityTypeFilter] = useState<EntityTypeFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceFilter>("all");
  const [editingItem, setEditingItem] = useState<KnowledgeReviewItem | null>(null);
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  const { data: batch, isLoading: batchLoading } = useKnowledgeReviewBatch(batchId);
  const { data: items, isLoading: itemsLoading } = useKnowledgeReviewItems({
    batchId,
    entityType: entityTypeFilter !== "all" ? entityTypeFilter : undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
    limit: 200,
  });

  const approveItem = useApproveItem(batchId);
  const rejectItem = useRejectItem(batchId);
  const editItem = useEditItem(batchId);
  const approveAllEligible = useApproveAllEligible(batchId);
  const exportIKP = useExportApprovedIKP(batchId);

  const filteredItems = (items ?? []).filter((item) => {
    if (confidenceFilter === "high" && item.confidence_score < 0.9) return false;
    if (
      confidenceFilter === "medium" &&
      (item.confidence_score < 0.7 || item.confidence_score >= 0.9)
    )
      return false;
    return true;
  });

  const handleApprove = async (item: KnowledgeReviewItem) => {
    try {
      await approveItem.mutateAsync({ itemId: item.id, body: {} });
      toast.success("Item approved.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve item.");
    }
  };

  const handleReject = async (item: KnowledgeReviewItem) => {
    const reason = rejectReason[item.id] ?? "";
    if (!reason.trim()) {
      toast.error("Please enter a rejection reason before rejecting.");
      return;
    }
    try {
      await rejectItem.mutateAsync({ itemId: item.id, body: { decision_reason: reason } });
      toast.success("Item rejected.");
      setRejectReason((prev) => {
        const next = { ...prev };
        delete next[item.id];
        return next;
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to reject item.");
    }
  };

  const handleEditSubmit = async (
    itemId: string,
    editedValue: string,
    reason: string
  ) => {
    try {
      await editItem.mutateAsync({
        itemId,
        body: { edited_value: editedValue, decision_reason: reason || undefined },
      });
      toast.success("Item edited and saved.");
      setEditingItem(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to edit item.");
    }
  };

  const handleApproveAll = async () => {
    try {
      const result = await approveAllEligible.mutateAsync();
      toast.success(`${result.newly_approved} item(s) auto-approved.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve all eligible items.");
    }
  };

  const handleExport = async () => {
    try {
      const result = await exportIKP.mutateAsync();
      toast.success(
        `Exported ${result.total_approved} items to ${result.export_path}`
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to export IKP.");
    }
  };

  if (batchLoading) {
    return (
      <div className="p-6 space-y-4 max-w-7xl mx-auto">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <p className="text-muted-foreground">Batch not found.</p>
      </div>
    );
  }

  const hasApprovedItems = batch.approved_count > 0;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Back navigation */}
      <Link
        href="/knowledge-review"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        All Batches
      </Link>

      {/* Batch header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {batch.batch_name}
          </h1>
          <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
            <ReviewStatusBadge status={batch.status} />
            <span>
              {batch.academic_year} / v{batch.ikp_version}
            </span>
            {batch.faculty_scope && <span>{batch.faculty_scope}</span>}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={handleApproveAll}
            disabled={approveAllEligible.isPending}
          >
            {approveAllEligible.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            Approve High-Confidence
          </Button>
          {hasApprovedItems && (
            <Button
              size="sm"
              onClick={handleExport}
              disabled={exportIKP.isPending}
            >
              {exportIKP.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Export Approved IKP
            </Button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total", value: batch.total_items, color: "text-foreground" },
          { label: "Approved", value: batch.approved_count, color: "text-green-700" },
          { label: "Rejected", value: batch.rejected_count, color: "text-red-700" },
          { label: "Pending", value: batch.pending_count, color: "text-blue-700" },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="rounded-xl border bg-card p-4 space-y-1"
          >
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-4">
        {/* Entity type */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Type:</span>
          {(["all", "programme", "module", "admission_requirement"] as const).map(
            (v) => (
              <button
                key={v}
                onClick={() => setEntityTypeFilter(v)}
                className={
                  entityTypeFilter === v
                    ? "px-2.5 py-1 rounded-full text-xs font-medium bg-primary text-primary-foreground"
                    : "px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground hover:text-foreground"
                }
              >
                {v === "all"
                  ? "All"
                  : v === "admission_requirement"
                  ? "Admission"
                  : v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            )
          )}
        </div>

        {/* Status */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Status:</span>
          {(["all", "pending_review", "approved", "rejected", "edited"] as const).map(
            (v) => (
              <button
                key={v}
                onClick={() => setStatusFilter(v)}
                className={
                  statusFilter === v
                    ? "px-2.5 py-1 rounded-full text-xs font-medium bg-primary text-primary-foreground"
                    : "px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground hover:text-foreground"
                }
              >
                {v === "all"
                  ? "All"
                  : v === "pending_review"
                  ? "Pending"
                  : v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            )
          )}
        </div>

        {/* Confidence */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Confidence:</span>
          {(["all", "high", "medium"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setConfidenceFilter(v)}
              className={
                confidenceFilter === v
                  ? "px-2.5 py-1 rounded-full text-xs font-medium bg-primary text-primary-foreground"
                  : "px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground hover:text-foreground"
              }
            >
              {v === "all" ? "All" : v === "high" ? "High ≥90%" : "Medium 70–89%"}
            </button>
          ))}
        </div>

        <span className="ml-auto text-xs text-muted-foreground self-center">
          {itemsLoading ? "Loading…" : `${filteredItems.length} items`}
        </span>
      </div>

      {/* Items table */}
      {itemsLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground text-sm">
          No items match the current filters.
        </div>
      ) : (
        <div className="rounded-xl border bg-card overflow-hidden overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Entity
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Field
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Value
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Source
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <Link
                      href={`/knowledge-review/items/${item.id}`}
                      className="font-medium hover:text-primary hover:underline line-clamp-1"
                    >
                      {item.entity_key}
                    </Link>
                    <p className="text-xs text-muted-foreground">{item.entity_type}</p>
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-muted-foreground">
                    {item.field_name}
                  </td>
                  <td className="px-4 py-3 max-w-[200px]">
                    <span className="font-mono text-xs line-clamp-2">
                      {item.edited_value ?? item.extracted_value}
                    </span>
                    {item.edited_value && (
                      <span className="text-xs text-purple-600 ml-1">(edited)</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge score={item.confidence_score} />
                  </td>
                  <td className="px-4 py-3">
                    <ReviewStatusBadge status={item.status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {item.source_document ? (
                      <span title={item.source_document}>
                        {item.source_document.length > 30
                          ? `…${item.source_document.slice(-27)}`
                          : item.source_document}
                        {item.page_number != null && ` p.${item.page_number}`}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {item.status === "pending_review" && (
                        <>
                          <Button
                            size="xs"
                            variant="ghost"
                            className="text-green-700 hover:text-green-800 hover:bg-green-50"
                            onClick={() => handleApprove(item)}
                            disabled={approveItem.isPending}
                          >
                            Approve
                          </Button>
                          <Button
                            size="xs"
                            variant="ghost"
                            className="text-destructive hover:bg-destructive/10"
                            onClick={() => handleReject(item)}
                            disabled={rejectItem.isPending}
                          >
                            Reject
                          </Button>
                        </>
                      )}
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => setEditingItem(item)}
                      >
                        Edit
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit dialog */}
      <EditValueDialog
        item={editingItem}
        open={editingItem !== null}
        onOpenChange={(open) => {
          if (!open) setEditingItem(null);
        }}
        onSubmit={handleEditSubmit}
        isPending={editItem.isPending}
      />
    </div>
  );
}
