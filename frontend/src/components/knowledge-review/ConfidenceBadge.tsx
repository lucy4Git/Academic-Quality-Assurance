"use client";

import { cn } from "@/lib/utils";

interface ConfidenceBadgeProps {
  score: number;
  className?: string;
}

/**
 * Color-coded confidence score badge.
 *
 * Green  >= 0.90  — high confidence (auto-approvable)
 * Yellow  0.70–0.89 — medium confidence (review recommended)
 * Red    < 0.70   — low confidence (manual review required)
 */
export function ConfidenceBadge({ score, className }: ConfidenceBadgeProps) {
  const pct = Math.round(score * 100);

  const color =
    score >= 0.9
      ? "bg-green-100 text-green-800 border-green-200"
      : score >= 0.7
      ? "bg-yellow-100 text-yellow-800 border-yellow-200"
      : "bg-red-100 text-red-800 border-red-200";

  const label =
    score >= 0.9 ? "High" : score >= 0.7 ? "Medium" : "Low";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
        color,
        className
      )}
      title={`Confidence: ${pct}% (${label})`}
    >
      {pct}%
    </span>
  );
}
