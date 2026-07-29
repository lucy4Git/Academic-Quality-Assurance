"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/auth.store";
import {
  useCurrentInstitution,
  useInstitutions,
} from "@/hooks/useInstitutions";
import {
  useInstitutionWorkspace,
  useTimeline,
  type TimelineEvent,
} from "@/hooks/useWorkspace";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  GraduationCap,
  BookOpen,
  Layers,
  Boxes,
  Users,
  CheckSquare,
  FileText,
  Brain,
  Clock,
  Upload,
  Search,
  BarChart2,
  ChevronRight,
} from "lucide-react";

const EVENT_ICONS: Record<string, React.ElementType> = {
  audit_triggered: CheckSquare,
  evidence_uploaded: Upload,
  knowledge_indexed: Brain,
  user_registered: Users,
  report_exported: BarChart2,
};

function StatCard({
  label,
  value,
  icon: Icon,
  colour,
  href,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  colour: string;
  href?: string;
}) {
  const inner = (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3 hover:shadow-md transition-shadow cursor-default">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</p>
        <div className={`rounded-lg p-2 ${colour}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="text-3xl font-bold text-foreground tabular-nums">{value.toLocaleString()}</p>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

function TimelineItem({ event }: { event: TimelineEvent }) {
  const Icon = EVENT_ICONS[event.event_type] ?? Clock;
  const relTime = new Date(event.occurred_at).toLocaleString();

  return (
    <div className="flex items-start gap-3 py-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground">{event.title}</p>
        <p className="text-xs text-muted-foreground truncate">{event.description}</p>
        <p className="text-[11px] text-muted-foreground/60 mt-0.5">{relTime}</p>
      </div>
    </div>
  );
}

export function InstitutionWorkspaceView() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "system_admin";
  const { data: currentInstitution } = useCurrentInstitution();
  const { data: institutions } = useInstitutions();

  const [selectedCode, setSelectedCode] = useState<string>("");

  useEffect(() => {
    if (isAdmin) {
      if (!selectedCode && institutions?.length) {
        setSelectedCode(institutions[0].code);
      }
      return;
    }

    setSelectedCode(currentInstitution?.code ?? "");
  }, [
    currentInstitution?.code,
    institutions,
    isAdmin,
    selectedCode,
    user?.id,
  ]);

  const { data: workspace, isLoading } = useInstitutionWorkspace(
    selectedCode || null
  );
  const { data: timeline } = useTimeline(20);

  const stats = workspace
    ? [
        { label: "Faculties", value: workspace.faculties, icon: Building2, colour: "bg-blue-100 text-blue-600", href: "/faculties" },
        { label: "Departments", value: workspace.departments, icon: Layers, colour: "bg-purple-100 text-purple-600", href: "/departments" },
        { label: "Programmes", value: workspace.programmes, icon: GraduationCap, colour: "bg-indigo-100 text-indigo-600", href: "/programmes" },
        { label: "Modules", value: workspace.modules, icon: BookOpen, colour: "bg-cyan-100 text-cyan-600", href: "/modules" },
        { label: "Total Audits", value: workspace.total_audits, icon: CheckSquare, colour: "bg-green-100 text-green-600", href: "/audits" },
        { label: "Evidence Files", value: workspace.evidence_files, icon: FileText, colour: "bg-amber-100 text-amber-600", href: "/files" },
        { label: "Active Users", value: workspace.active_users, icon: Users, colour: "bg-rose-100 text-rose-600", href: "/users" },
        { label: "Knowledge Chunks", value: workspace.knowledge_chunks, icon: Boxes, colour: "bg-teal-100 text-teal-600" },
      ]
    : [];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {workspace ? workspace.institution_name : "Institution Workspace"}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {workspace
              ? `${workspace.institution_code} · ${workspace.institution_type} institution`
              : "Overview of your institution's QA activity"}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isAdmin && (
            <select
              value={selectedCode}
              onChange={(e) => setSelectedCode(e.target.value)}
              className="rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {institutions?.map((institution) => (
                <option key={institution.id} value={institution.code}>
                  {institution.code} — {institution.name}
                </option>
              ))}
            </select>
          )}
          <Link
            href="/ai-workspace"
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
          >
            <Brain className="h-4 w-4" />
            Ask AI
          </Link>
        </div>
      </div>

      {/* Stats grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {stats.map((s) => (
            <StatCard key={s.label} {...s} />
          ))}
        </div>
      )}

      {/* Compliance summary */}
      {workspace && workspace.total_audits > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="text-sm font-semibold text-foreground mb-3">Audit Completion</p>
          <div className="flex items-center gap-4">
            <div className="flex-1 h-3 rounded-full bg-muted overflow-hidden">
              <div
                className="h-3 rounded-full bg-green-500 transition-all"
                style={{ width: `${Math.round((workspace.completed_audits / workspace.total_audits) * 100)}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-foreground tabular-nums whitespace-nowrap">
              {workspace.completed_audits} / {workspace.total_audits} completed
            </span>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">Quick actions</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Run Audit", href: "/audits/new", icon: CheckSquare },
            { label: "Upload Evidence", href: "/files/upload", icon: Upload },
            { label: "Knowledge Search", href: "/knowledge-search", icon: Search },
            { label: "View Reports", href: "/reports", icon: BarChart2 },
          ].map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-foreground hover:border-indigo-300 hover:bg-indigo-50/50 transition-all group"
            >
              <div className="flex items-center gap-2">
                <a.icon className="h-4 w-4 text-muted-foreground group-hover:text-indigo-600" />
                {a.label}
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-indigo-400" />
            </Link>
          ))}
        </div>
      </div>

      {/* Activity timeline */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-foreground">Recent Activity</p>
          <span className="text-xs text-muted-foreground">{timeline?.length ?? 0} events</span>
        </div>
        {!timeline || timeline.length === 0 ? (
          <div className="py-8 text-center">
            <Clock className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No recent activity</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {timeline.slice(0, 10).map((ev) => (
              <TimelineItem key={ev.id} event={ev} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
