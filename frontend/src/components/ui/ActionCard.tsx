import Link from "next/link";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface ActionCardProps {
  label: string;
  description: string;
  icon: LucideIcon;
  href: string;
  iconClassName?: string;
}

export function ActionCard({
  label,
  description,
  icon: Icon,
  href,
  iconClassName = "bg-indigo-50 text-indigo-600",
}: ActionCardProps) {
  return (
    <Link
      href={href}
      className="group flex items-start gap-4 rounded-xl border border-border bg-card p-4 transition-all hover:shadow-md hover:border-primary/30"
    >
      <div className={cn("flex-shrink-0 rounded-lg p-2.5 transition-colors", iconClassName)}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
          {label}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{description}</p>
      </div>
    </Link>
  );
}
