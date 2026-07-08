"use client";

import Link from "next/link";
import {
  Library,
  Upload,
  SearchCheck,
  AlertTriangle,
  ShieldCheck,
  Shield,
  BookOpen,
  ClipboardCheck,
  ArrowRight,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

const STAFF: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"];
const COORDINATOR_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"];
const DEAN_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean"];
const QA_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer"];

interface WorkspaceCard {
  label: string;
  description: string;
  href: string;
  icon: React.ElementType;
  iconColor: string;
  badge?: string;
  roles: UserRole[];
}

const CARDS: WorkspaceCard[] = [
  {
    label: "Audits",
    description: "AI-powered audit execution across all agent types — module and programme scoped",
    href: "/audits",
    icon: SearchCheck,
    iconColor: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50",
    badge: "Core",
    roles: COORDINATOR_AND_ABOVE,
  },
  {
    label: "Evidence",
    description: "Upload, manage and verify evidence files and supporting documentation",
    href: "/files",
    icon: Library,
    iconColor: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    badge: "Files",
    roles: STAFF,
  },
  {
    label: "Upload Evidence",
    description: "Submit audit evidence packages and folder structures for AI verification",
    href: "/files/upload",
    icon: Upload,
    iconColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50",
    badge: "Upload",
    roles: COORDINATOR_AND_ABOVE,
  },
  {
    label: "Findings",
    description: "Review, track and respond to audit findings across all compliance areas",
    href: "/findings",
    icon: AlertTriangle,
    iconColor: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
    badge: "Findings",
    roles: STAFF,
  },
  {
    label: "Compliance",
    description: "Compliance reports, dashboards and monitoring across institutions",
    href: "/reports/compliance",
    icon: ClipboardCheck,
    iconColor: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50",
    badge: "Reports",
    roles: DEAN_AND_ABOVE,
  },
  {
    label: "Accreditation",
    description: "Accreditation readiness assessments and body submission management",
    href: "/accreditation",
    icon: Shield,
    iconColor: "text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50",
    badge: "CHE/DHET",
    roles: DEAN_AND_ABOVE,
  },
  {
    label: "Programme Review",
    description: "AI-powered programme review audits with accreditation alignment",
    href: "/audits",
    icon: BookOpen,
    iconColor: "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50",
    badge: "Programme",
    roles: COORDINATOR_AND_ABOVE,
  },
  {
    label: "Policy Review",
    description: "Review, update and approve institutional quality policy documents",
    href: "/knowledge-review",
    icon: ShieldCheck,
    iconColor: "text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50",
    badge: "Policy",
    roles: QA_AND_ABOVE,
  },
];

export default function QualityWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));

  return (
    <div className="max-w-[1100px] space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center flex-shrink-0">
          <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Quality</h1>
          <p className="text-muted-foreground mt-1 text-sm leading-relaxed">
            Evidence, audits, findings, compliance, accreditation and programme reviews.
          </p>
        </div>
      </div>

      {/* Card grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {visible.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href + card.label}
              href={card.href}
              className="aqaa-card group flex flex-col gap-4 p-6 hover:border-primary/25 hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className={cn("w-9 h-9 rounded-xl flex items-center justify-center", card.iconColor)}>
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </div>
                {card.badge && (
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/60 px-2 py-0.5 bg-muted rounded-full">
                    {card.badge}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground">{card.label}</p>
                <p className="text-[12.5px] text-muted-foreground mt-1.5 leading-relaxed">{card.description}</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-primary/70 font-medium group-hover:text-primary group-hover:gap-2 transition-all">
                Open <ArrowRight className="h-3 w-3" aria-hidden="true" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
