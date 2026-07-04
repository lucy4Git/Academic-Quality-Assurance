"use client";

import Link from "next/link";
import {
  Building2,
  GraduationCap,
  BookOpen,
  Layers,
  Boxes,
  Users,
  GitBranch,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useWorkflows } from "@/hooks/useWorkflow";
import { useRole } from "@/hooks/useRole";
import { cn } from "@/lib/utils";
import {
  WORKFLOW_STATUS_LABELS,
  WORKFLOW_STATUS_COLOURS,
  type WorkflowStatus,
  type WorkflowItem,
} from "@/types";

interface StatCardProps {
  label: string;
  value: number | undefined;
  isLoading: boolean;
  icon: React.ElementType;
  href?: string;
  colour: string;
}

function StatCard({ label, value, isLoading, icon: Icon, href, colour }: StatCardProps) {
  const content = (
    <div className={cn(
      "rounded-xl border border-border bg-card p-5 flex flex-col gap-3 transition-shadow",
      href && "hover:shadow-md cursor-pointer"
    )}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {label}
        </p>
        <div className={cn("rounded-lg p-2", colour)}>
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
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

// ---------------------------------------------------------------------------
// Workflow summary widget
// ---------------------------------------------------------------------------

function WorkflowSummary() {
  const { data, isLoading } = useWorkflows();

  const counts: Partial<Record<WorkflowStatus, number>> = {};
  for (const item of data ?? []) {
    counts[item.workflow_status] = (counts[item.workflow_status] ?? 0) + 1;
  }

  const activeStatuses: WorkflowStatus[] = [
    "assigned", "evidence_collection", "pending_qa_review", "returned_for_corrections",
  ];

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <p className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" /> Workflow Summary
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {activeStatuses.map((s) => <Skeleton key={s} className="h-12 rounded-lg" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-foreground flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" /> Workflow Summary
        </p>
        <Link href="/workflow" className="text-xs text-primary hover:underline">View all →</Link>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {activeStatuses.map((status) => (
          <Link
            key={status}
            href={`/workflow?workflow_status=${status}`}
            className={cn(
              "rounded-lg border px-3 py-2 flex flex-col gap-1 transition-shadow hover:shadow-sm",
              WORKFLOW_STATUS_COLOURS[status],
            )}
          >
            <span className="text-2xl font-bold tabular-nums">{counts[status] ?? 0}</span>
            <span className="text-[11px] font-medium leading-tight">{WORKFLOW_STATUS_LABELS[status]}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function DashboardView() {
  const { data, isLoading } = useDashboardSummary();
  const { isSysAdmin, isQAOfficer, isDean, isHOD, isCoordinator } = useRole();

  const cards: StatCardProps[] = [
    {
      label: "Institutions",
      value: data?.institutions,
      isLoading,
      icon: Building2,
      href: (isSysAdmin || isQAOfficer) ? "/institutions" : undefined,
      colour: "bg-blue-50 text-blue-600",
    },
    {
      label: "Faculties",
      value: data?.faculties,
      isLoading,
      icon: GraduationCap,
      href: isDean ? "/faculties" : undefined,
      colour: "bg-purple-50 text-purple-600",
    },
    {
      label: "Departments",
      value: data?.departments,
      isLoading,
      icon: BookOpen,
      href: isHOD ? "/departments" : undefined,
      colour: "bg-amber-50 text-amber-600",
    },
    {
      label: "Programmes",
      value: data?.programmes,
      isLoading,
      icon: Layers,
      href: "/programmes",
      colour: "bg-green-50 text-green-600",
    },
    {
      label: "Modules",
      value: data?.modules,
      isLoading,
      icon: Boxes,
      href: "/modules",
      colour: "bg-red-50 text-red-600",
    },
    {
      label: "Users",
      value: data?.users,
      isLoading,
      icon: Users,
      href: isSysAdmin ? "/users" : undefined,
      colour: "bg-slate-50 text-slate-600",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Welcome to the Academic Quality Assurance Agent platform.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {cards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {isCoordinator && <WorkflowSummary />}
    </div>
  );
}
