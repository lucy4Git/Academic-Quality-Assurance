import { cn } from "@/lib/utils";

type StatusVariant =
  | "success"
  | "warning"
  | "error"
  | "info"
  | "neutral"
  | "purple";

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
  error:   "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
  info:    "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
  neutral: "bg-muted text-muted-foreground border-border",
  purple:  "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800",
};

const DOT_CLASSES: Record<StatusVariant, string> = {
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error:   "bg-red-500",
  info:    "bg-blue-500",
  neutral: "bg-muted-foreground",
  purple:  "bg-purple-500",
};

interface StatusBadgeProps {
  label: string;
  variant?: StatusVariant;
  showDot?: boolean;
  className?: string;
}

export function StatusBadge({
  label,
  variant = "neutral",
  showDot = true,
  className,
}: StatusBadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border",
      VARIANT_CLASSES[variant],
      className
    )}>
      {showDot && <span className={cn("h-1.5 w-1.5 rounded-full flex-shrink-0", DOT_CLASSES[variant])} />}
      {label}
    </span>
  );
}
