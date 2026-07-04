"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfidenceBadge } from "@/components/knowledge-review/ConfidenceBadge";
import { ReviewStatusBadge } from "@/components/knowledge-review/ReviewStatusBadge";
import {
  useKnowledgeReviewItem,
  useApproveItem,
  useRejectItem,
  useEditItem,
} from "@/hooks/useKnowledgeReview";

interface ItemReviewDetailProps {
  itemId: string;
}

export function ItemReviewDetail({ itemId }: ItemReviewDetailProps) {
  const { data: item, isLoading } = useKnowledgeReviewItem(itemId);
  const [rejectReason, setRejectReason] = useState("");
  const [editedValue, setEditedValue] = useState("");
  const [editReason, setEditReason] = useState("");
  const [showEdit, setShowEdit] = useState(false);

  const batchId = item?.batch_id ?? "";
  const approveItem = useApproveItem(batchId);
  const rejectItem = useRejectItem(batchId);
  const editItem = useEditItem(batchId);

  const handleApprove = async () => {
    if (!item) return;
    try {
      await approveItem.mutateAsync({ itemId: item.id, body: {} });
      toast.success("Item approved.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve.");
    }
  };

  const handleReject = async () => {
    if (!item) return;
    if (!rejectReason.trim()) {
      toast.error("A rejection reason is required.");
      return;
    }
    try {
      await rejectItem.mutateAsync({ itemId: item.id, body: { decision_reason: rejectReason } });
      toast.success("Item rejected.");
      setRejectReason("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to reject.");
    }
  };

  const handleEdit = async () => {
    if (!item || !editedValue.trim()) return;
    try {
      await editItem.mutateAsync({
        itemId: item.id,
        body: {
          edited_value: editedValue.trim(),
          decision_reason: editReason.trim() || undefined,
        },
      });
      toast.success("Item edited.");
      setShowEdit(false);
      setEditedValue("");
      setEditReason("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to edit item.");
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <p className="text-muted-foreground">Item not found.</p>
      </div>
    );
  }

  const isDecided = ["approved", "rejected", "edited"].includes(item.status);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Navigation */}
      <Link
        href={`/knowledge-review/${item.batch_id}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Batch
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{item.entity_key}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm text-muted-foreground capitalize">
              {item.entity_type.replace("_", " ")}
            </span>
            <ReviewStatusBadge status={item.status} />
          </div>
        </div>
        <ConfidenceBadge score={item.confidence_score} className="text-sm" />
      </div>

      {/* Main details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Extracted data */}
        <div className="rounded-xl border bg-card p-5 space-y-4">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
            Extracted Data
          </h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Field</dt>
              <dd className="font-mono mt-0.5">{item.field_name}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Extracted Value</dt>
              <dd className="font-mono mt-0.5 bg-muted/50 rounded px-2 py-1">
                {item.extracted_value}
              </dd>
            </div>
            {item.edited_value && (
              <div>
                <dt className="text-muted-foreground text-purple-600">Edited Value</dt>
                <dd className="font-mono mt-0.5 bg-purple-50 text-purple-900 rounded px-2 py-1">
                  {item.edited_value}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-muted-foreground">Confidence</dt>
              <dd className="mt-0.5">
                <ConfidenceBadge score={item.confidence_score} />
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Extraction Method</dt>
              <dd className="font-mono mt-0.5 text-xs">
                {item.extraction_method ?? "—"}
              </dd>
            </div>
          </dl>
        </div>

        {/* Provenance */}
        <div className="rounded-xl border bg-card p-5 space-y-4">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
            Provenance
          </h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Source Document</dt>
              <dd className="font-mono text-xs mt-0.5 break-all">
                {item.source_document ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Page Number</dt>
              <dd className="mt-0.5">
                {item.page_number != null ? `Page ${item.page_number}` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Academic Year</dt>
              <dd className="mt-0.5">{item.academic_year ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">IKP Version</dt>
              <dd className="mt-0.5">{item.ikp_version ? `v${item.ikp_version}` : "—"}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Decision history */}
      {isDecided && (
        <div className="rounded-xl border bg-card p-5 space-y-3">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
            Decision History
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <dt className="text-muted-foreground w-28">Decision</dt>
              <dd>
                <ReviewStatusBadge status={item.status} />
              </dd>
            </div>
            {item.reviewed_at && (
              <div className="flex items-center gap-3">
                <dt className="text-muted-foreground w-28">Reviewed At</dt>
                <dd>{new Date(item.reviewed_at).toLocaleString("en-ZA")}</dd>
              </div>
            )}
            {item.decision_reason && (
              <div className="flex gap-3">
                <dt className="text-muted-foreground w-28 flex-shrink-0">Reason</dt>
                <dd className="text-foreground">{item.decision_reason}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Decision panel */}
      {!isDecided && (
        <div className="rounded-xl border bg-card p-5 space-y-4">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
            Make a Decision
          </h2>

          {!showEdit ? (
            <div className="space-y-4">
              {/* Approve */}
              <div className="flex items-center gap-3">
                <Button
                  onClick={handleApprove}
                  disabled={approveItem.isPending}
                  className="gap-1.5"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {approveItem.isPending ? "Approving…" : "Approve"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowEdit(true);
                    setEditedValue(item.extracted_value);
                  }}
                >
                  Edit Value
                </Button>
              </div>

              {/* Reject */}
              <div className="space-y-2">
                <Label htmlFor="reject-reason">Rejection Reason (required to reject)</Label>
                <Textarea
                  id="reject-reason"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Explain why this extracted value should be rejected…"
                  rows={2}
                  className="resize-none"
                />
                <Button
                  variant="destructive"
                  onClick={handleReject}
                  disabled={rejectItem.isPending || !rejectReason.trim()}
                  className="gap-1.5"
                >
                  <XCircle className="h-4 w-4" />
                  {rejectItem.isPending ? "Rejecting…" : "Reject"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="edit-value">Corrected Value</Label>
                <Textarea
                  id="edit-value"
                  value={editedValue}
                  onChange={(e) => setEditedValue(e.target.value)}
                  rows={3}
                  className="font-mono text-sm resize-none"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-reason-detail">Reason (optional)</Label>
                <Textarea
                  id="edit-reason-detail"
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  placeholder="Why was this value corrected?"
                  rows={2}
                  className="resize-none"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleEdit}
                  disabled={editItem.isPending || !editedValue.trim()}
                >
                  {editItem.isPending ? "Saving…" : "Save Edit"}
                </Button>
                <Button variant="outline" onClick={() => setShowEdit(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
