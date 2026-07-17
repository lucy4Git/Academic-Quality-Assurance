"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

/** Map path segments to human-readable labels */
const SEGMENT_LABELS: Record<string, string> = {
  dashboard: "Home",
  workspace: "Workspace",
  knowledge: "Knowledge",
  quality: "Quality",
  administration: "Administration",
  ai: "AI",
  extraction: "Extraction Review",
  acquisition: "Acquisition",
  institutions: "Institutions",
  faculties: "Faculties",
  departments: "Departments",
  programmes: "Programmes",
  modules: "Modules",
  files: "Files",
  upload: "Upload Evidence",
  audits: "Audit Centre",
  findings: "Findings",
  reports: "Reports",
  compliance: "Compliance",
  trends: "Trends",
  evidence: "Evidence Coverage",
  export: "Export",
  accreditation: "Accreditation",
  compare: "Cycle Comparison",
  notifications: "Notifications",
  users: "Users",
  invite: "Invite User",
  activity: "Activity Log",
  settings: "Settings",
  profile: "Profile",
  security: "Security",
  system: "System",
  email: "Email / SMTP",
  storage: "Storage",
  integrations: "Integrations",
  "audit-history": "Audit History",
  report: "Report",
  new: "New",
  edit: "Edit",
  versions: "Versions",
  forbidden: "Access Denied",
};

interface Crumb {
  label: string;
  href: string;
  isLast: boolean;
}

function buildCrumbs(pathname: string): Crumb[] {
  const segments = pathname.split("/").filter(Boolean);

  const crumbs: Crumb[] = [];
  let accumulated = "";

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    accumulated += `/${seg}`;
    const isLast = i === segments.length - 1;

    // Detect UUID-like segments (resource IDs) — show generic label
    const isId = /^[0-9a-f-]{8,}$/i.test(seg);
    const label = isId
      ? "Detail"
      : SEGMENT_LABELS[seg] ?? seg.charAt(0).toUpperCase() + seg.slice(1);

    crumbs.push({ label, href: accumulated, isLast });
  }

  return crumbs;
}

export function Breadcrumb({ className }: { className?: string }) {
  const pathname = usePathname();
  const crumbs = buildCrumbs(pathname);

  if (crumbs.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center text-sm", className)}
    >
      <ol className="flex items-center gap-1 flex-wrap">
        {/* Home */}
        <li>
          <Link
            href="/dashboard"
            className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded"
            aria-label="Dashboard"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
        </li>

        {crumbs.map((crumb) => (
          <li key={crumb.href} className="flex items-center gap-1">
            <ChevronRight className="h-3 w-3 text-muted-foreground/50 flex-shrink-0" />
            {crumb.isLast ? (
              <span
                className="text-foreground font-medium truncate max-w-[180px]"
                aria-current="page"
              >
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[120px]"
              >
                {crumb.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
