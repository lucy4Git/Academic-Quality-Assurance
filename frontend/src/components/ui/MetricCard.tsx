import Link from "next/link";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: number | string | undefined;
  isLoading?: boolean;
  icon: LucideIcon;
  href?: string;
  iconClassName?: string;
  trend?: { value: number; label: string };
}

export function MetricCard({
  label,
  value,
  isLoading,
  icon: Icon,
  href,
  iconClassName = "bg-muted text-muted-foreground",
  trend,
}: MetricCardProps) {
  const content = (
    <div className={cn(
      "rounded-xl border border-border bg-card p-5 flex flex-col gap-3 transition-shadow",
      href && "hover:shadow-md cursor-pointer"
    )}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</p>
        <div className={cn("rounded-lg p-2", iconClassName)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      {isLoading ? (
        <Skeleton className="h-8 w-16" />
      ) : (
        <p className="text-3xl font-bold text-foreground tabular-nums">
          {value?.toLocaleString() ?? "—"}
        </p>
      )}
      {trend && !isLoading && (
        <p className={cn("text-xs font-medium", trend.value >= 0 ? "text-emerald-600" : "text-destructive")}>
          {trend.value >= 0 ? "+" : ""}{trend.value} {trend.label}
        </p>
      )}
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}
