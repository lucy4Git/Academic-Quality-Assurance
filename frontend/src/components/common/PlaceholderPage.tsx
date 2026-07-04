import { Construction } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description?: string;
}

/**
 * Temporary placeholder rendered for routes that are not yet implemented.
 * Prevents 404 errors while keeping the AppShell and navigation intact.
 */
export function PlaceholderPage({
  title,
  description = "This module is scheduled for a later AQAA phase.",
}: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {title}
        </h1>
      </div>
      <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center justify-center text-center gap-4">
        <div className="rounded-full bg-muted p-4">
          <Construction className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
        </div>
        <p className="text-muted-foreground max-w-sm">{description}</p>
      </div>
    </div>
  );
}
