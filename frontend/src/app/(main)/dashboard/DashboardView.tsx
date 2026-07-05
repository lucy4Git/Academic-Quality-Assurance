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
  Upload,
  BrainCircuit,
  SearchCheck,
  ClipboardCheck,
  Zap,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useWorkflows } from "@/hooks/useWorkflow";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import { cn } from "@/lib/utils";
import {
  WORKFLOW_STATUS_LABELS,
  WORKFLOW_STATUS_COLOURS,
  type WorkflowStatus,
} from "@/types";

// ── Stat card ────────────────────────────────────────────────────────────────

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
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</p>
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

// ── Workflow summary ─────────────────────────────────────────────────────────

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

// ── Quick actions ────────────────────────────────────────────────────────────

interface QuickAction {
  label: string;
  description: string;
  href: string;
  icon: React.ElementType;
  iconColour: string;
  show: boolean;
}

function QuickActions({ actions }: { actions: QuickAction[] }) {
  const visible = actions.filter((a) => a.show);
  if (visible.length === 0) return null;

  return (
    <div>
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-widest mb-3">
        Quick Actions
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {visible.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="group flex items-start gap-3 rounded-xl border border-border bg-card p-4 transition-all hover:shadow-md hover:border-primary/30"
          >
            <div className={cn("flex-shrink-0 rounded-lg p-2 transition-colors", action.iconColour)}>
              <action.icon className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                {action.label}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{action.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ── AI status banner ─────────────────────────────────────────────────────────

function AIStatusBanner({ isStaff }: { isStaff: boolean }) {
  if (!isStaff) return null;
  return (
    <div className="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 p-4 flex items-center gap-4">
      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center">
        <Zap className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
          AI Systems Operational
        </p>
        <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-0.5">
          All 8 AI audit agents are ready. Knowledge base indexed and available.
        </p>
      </div>
      <Link
        href="/ai-workspace"
        className="flex-shrink-0 text-xs font-semibold text-emerald-700 dark:text-emerald-300 hover:underline"
      >
        Open Workspace →
      </Link>
    </div>
  );
}

// ── Main view ────────────────────────────────────────────────────────────────

export function DashboardView() {
  const { data, isLoading } = useDashboardSummary();
  const { isSysAdmin, isQAOfficer, isDean, isHOD, isCoordinator, isLecturer } = useRole();
  const user = useAuthStore((s) => s.user);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  const statCards: StatCardProps[] = [
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

  const quickActions: QuickAction[] = [
    {
      label: "Upload Evidence",
      description: "Submit module documents and evidence files",
      href: "/files/upload",
      icon: Upload,
      iconColour: "bg-indigo-50 text-indigo-600",
      show: isLecturer,
    },
    {
      label: "Start AI Audit",
      description: "Trigger a quality audit for a module or programme",
      href: "/audits",
      icon: ClipboardCheck,
      iconColour: "bg-amber-50 text-amber-600",
      show: isCoordinator,
    },
    {
      label: "Knowledge Search",
      description: "Query the institution knowledge base with AI",
      href: "/knowledge-search",
      icon: SearchCheck,
      iconColour: "bg-emerald-50 text-emerald-600",
      show: isLecturer,
    },
    {
      label: "AI QA Assistant",
      description: "Ask the AI assistant quality assurance questions",
      href: "/ai-assistant",
      icon: BrainCircuit,
      iconColour: "bg-purple-50 text-purple-600",
      show: isLecturer,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header / greeting */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          {greeting}, {firstName}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Here&apos;s your AQAA platform overview for today.
        </p>
      </div>

      {/* AI status banner */}
      <AIStatusBanner isStaff={isLecturer} />

      {/* Platform statistics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {/* Quick actions */}
      <QuickActions actions={quickActions} />

      {/* Workflow summary */}
      {isCoordinator && <WorkflowSummary />}
    </div>
  );
}
