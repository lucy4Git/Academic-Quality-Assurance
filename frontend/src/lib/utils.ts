import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { AuditStatus, FindingSeverity, UploadState, AuditRunStatus } from "@/types";

/** Merge Tailwind class names safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format bytes to human-readable string */
export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/** Format ISO date string to readable format */
export function formatDate(iso: string, opts?: Intl.DateTimeFormatOptions): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...opts,
  });
}

/** Format ISO datetime string to readable format */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format a compliance score as a percentage string */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return `${score.toFixed(1)}%`;
}

/** Return days since an ISO date */
export function daysAgo(iso: string): number {
  const ms = Date.now() - new Date(iso).getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

/** Convert snake_case to Title Case */
export function toTitleCase(str: string): string {
  return str
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Return Tailwind colour classes for a compliance score */
export function complianceColour(score: number | null | undefined): {
  bar: string;
  text: string;
  bg: string;
  badge: string;
} {
  if (score === null || score === undefined) {
    return {
      bar: "bg-slate-300",
      text: "text-slate-600",
      bg: "bg-slate-50",
      badge: "text-slate-600 bg-slate-100 border-slate-200",
    };
  }
  if (score >= 90) {
    return {
      bar: "bg-green-500",
      text: "text-green-700",
      bg: "bg-green-50",
      badge: "text-green-700 bg-green-50 border-green-200",
    };
  }
  if (score >= 70) {
    return {
      bar: "bg-amber-400",
      text: "text-amber-700",
      bg: "bg-amber-50",
      badge: "text-amber-700 bg-amber-50 border-amber-200",
    };
  }
  if (score >= 50) {
    return {
      bar: "bg-orange-400",
      text: "text-orange-700",
      bg: "bg-orange-50",
      badge: "text-orange-700 bg-orange-50 border-orange-200",
    };
  }
  return {
    bar: "bg-red-500",
    text: "text-red-700",
    bg: "bg-red-50",
    badge: "text-red-700 bg-red-50 border-red-200",
  };
}

/** Return Tailwind colour classes for AuditStatus */
export function auditStatusColour(status: AuditStatus | null | undefined): string {
  switch (status) {
    case "compliant":
      return "text-green-700 bg-green-50 border-green-200";
    case "needs_attention":
      return "text-amber-700 bg-amber-50 border-amber-200";
    case "non_compliant":
      return "text-orange-700 bg-orange-50 border-orange-200";
    case "critical":
      return "text-red-700 bg-red-50 border-red-200";
    default:
      return "text-slate-600 bg-slate-50 border-slate-200";
  }
}

/** Return Tailwind colour classes for FindingSeverity */
export function severityColour(severity: FindingSeverity): string {
  switch (severity) {
    case "critical":
      return "text-red-700 bg-red-50 border-red-200";
    case "high":
      return "text-orange-700 bg-orange-50 border-orange-200";
    case "medium":
      return "text-amber-700 bg-amber-50 border-amber-200";
    case "low":
      return "text-blue-700 bg-blue-50 border-blue-200";
    case "info":
      return "text-slate-600 bg-slate-50 border-slate-200";
  }
}

/** Return Tailwind colour classes for AuditRunStatus */
export function runStatusColour(status: AuditRunStatus): string {
  switch (status) {
    case "completed":
      return "text-green-700 bg-green-50 border-green-200";
    case "running":
      return "text-blue-700 bg-blue-50 border-blue-200";
    case "pending":
      return "text-slate-600 bg-slate-50 border-slate-200";
    case "failed":
      return "text-red-700 bg-red-50 border-red-200";
  }
}

/** Return Tailwind colour classes for UploadState */
export function uploadStateColour(state: UploadState): string {
  switch (state) {
    case "ready":
      return "text-green-700 bg-green-50 border-green-200";
    case "scanning":
      return "text-blue-700 bg-blue-50 border-blue-200";
    case "pending":
      return "text-slate-600 bg-slate-50 border-slate-200";
    case "quarantined":
    case "failed":
      return "text-red-700 bg-red-50 border-red-200";
  }
}
