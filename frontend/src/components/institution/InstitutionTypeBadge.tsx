"use client";

import { cn } from "@/lib/utils";

interface InstitutionTypeBadgeProps {
  institutionType: "pilot" | "demo" | "production" | string;
  isActive?: boolean;
  className?: string;
  size?: "sm" | "xs";
}

const TYPE_CONFIG: Record<string, { label: string; className: string }> = {
  pilot: {
    label: "Pilot",
    className: "bg-blue-100 text-blue-700 border-blue-200",
  },
  demo: {
    label: "Archived Demo",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
  production: {
    label: "Production",
    className: "bg-green-100 text-green-700 border-green-200",
  },
};

export function InstitutionTypeBadge({
  institutionType,
  isActive = true,
  className,
  size = "sm",
}: InstitutionTypeBadgeProps) {
  const config = TYPE_CONFIG[institutionType] ?? TYPE_CONFIG.production;
  const label = !isActive ? "Archived" : config.label;
  const badgeClass = !isActive
    ? "bg-gray-100 text-gray-500 border-gray-200"
    : config.className;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border font-medium",
        size === "xs" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs",
        badgeClass,
        className
      )}
    >
      {label}
    </span>
  );
}
