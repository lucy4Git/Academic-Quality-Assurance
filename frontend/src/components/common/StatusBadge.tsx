import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  label: string;
  className?: string;
}

export function StatusBadge({ label, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        className
      )}
    >
      {label}
    </span>
  );
}

interface ComplianceBarProps {
  score: number | null | undefined;
  showLabel?: boolean;
  className?: string;
}

export function ComplianceBar({
  score,
  showLabel = true,
  className,
}: ComplianceBarProps) {
  if (score === null || score === undefined) {
    return (
      <span className="text-xs text-muted-foreground italic">No data</span>
    );
  }

  let barColour = "bg-red-500";
  let textColour = "text-red-700";
  if (score >= 90) { barColour = "bg-green-500"; textColour = "text-green-700"; }
  else if (score >= 70) { barColour = "bg-amber-400"; textColour = "text-amber-700"; }
  else if (score >= 50) { barColour = "bg-orange-400"; textColour = "text-orange-700"; }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden min-w-[60px]">
        <div
          className={cn("h-full rounded-full transition-all", barColour)}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn("text-xs font-medium tabular-nums w-10 text-right", textColour)}>
          {score.toFixed(1)}%
        </span>
      )}
    </div>
  );
}
