"use client";

import { cn } from "@/lib/utils";
import type { ReviewBatchStatus, ReviewItemStatus } from "@/types/knowledge-review";

interface ReviewStatusBadgeProps {
  status: ReviewItemStatus | ReviewBatchStatus;
  className?: string;
}

const STATUS_STYLES: Record<string, string> = {
  // Item statuses
  pending_review: "bg-blue-100 text-blue-800 border-blue-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  edited: "bg-purple-100 text-purple-800 border-purple-200",
  quarantined: "bg-orange-100 text-orange-800 border-orange-200",
  imported: "bg-gray-100 text-gray-700 border-gray-200",
  // Batch statuses
  open: "bg-blue-100 text-blue-800 border-blue-200",
  in_review: "bg-yellow-100 text-yellow-800 border-yellow-200",
  exported: "bg-emerald-100 text-emerald-800 border-emerald-200",
  closed: "bg-gray-100 text-gray-700 border-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pending Review",
  approved: "Approved",
  rejected: "Rejected",
  edited: "Edited",
  quarantined: "Quarantined",
  imported: "Imported",
  open: "Open",
  in_review: "In Review",
  exported: "Exported",
  closed: "Closed",
};

export function ReviewStatusBadge({ status, className }: ReviewStatusBadgeProps) {
  const style =
    STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700 border-gray-200";
  const label = STATUS_LABELS[status] ?? status;

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        style,
        className
      )}
    >
      {label}
    </span>
  );
}
