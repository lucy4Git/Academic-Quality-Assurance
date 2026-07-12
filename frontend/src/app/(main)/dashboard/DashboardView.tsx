"use client";

import { memo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Brain,
  ArrowRight,
  Upload,
  Play,
  FileBarChart2,
  BookOpen,
  ShieldCheck,
  Sparkles,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Search,
  ChevronRight,
  GraduationCap,
  Users,
  Building2,
  Cpu,
} from "lucide-react";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import { useInstitutions } from "@/hooks/useInstitutions";
import { ROLE_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

// ── Greeting logic ────────────────────────────────────────────────────────────

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 5) return "Good night";
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

// ── Role-specific suggested prompts ──────────────────────────────────────────

const ROLE_PROMPTS: Partial<Record<UserRole, string[]>> = {
  system_admin: [
    "Compare compliance scores across all institutions",
    "Which institution has the most open audit findings?",
    "Summarise AI provider usage and token consumption",
    "Show accreditation readiness across all faculties",
  ],
  quality_assurance_officer: [
    "Summarise recent audit findings for Engineering",
    "Which modules need evidence before Friday?",
    "What is the accreditation status of my institution?",
    "Compare NQF levels across active programmes",
  ],
  faculty_dean: [
    "Which programmes in my faculty need attention?",
    "Summarise compliance status across departments",
    "What audit findings are outstanding this semester?",
    "Generate an accreditation readiness summary for my faculty",
  ],
  head_of_department: [
    "Which modules in my department have open findings?",
    "What evidence is missing before the next audit cycle?",
    "Summarise lecturer compliance for this semester",
    "Show NQF alignment for all active modules",
  ],
  programme_coordinator: [
    "Run Assessment Compliance audit for CSC401",
    "Which modules need evidence uploaded?",
    "Summarise audit findings for my programme",
    "What is the accreditation readiness of my programme?",
  ],
  lecturer: [
    "What evidence do I need to upload for my modules?",
    "Summarise my module's audit findings",
    "What is the compliance status of my modules?",
    "Help me understand the assessment policy",
  ],
  student: [
    "What programmes does my institution offer?",
    "Explain the academic quality assurance process",
    "What NQF level is my programme?",
    "What resources are available for students?",
  ],
};

function getPromptsForRole(role?: UserRole): string[] {
  if (!role) return ROLE_PROMPTS.quality_assurance_officer!;
  return ROLE_PROMPTS[role] ?? ROLE_PROMPTS.lecturer!;
}

// ── Ask AQAA composer — shown for ALL roles ───────────────────────────────────

function AskAQAAComposer({ role }: { role?: UserRole }) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const prompts = getPromptsForRole(role);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/ai-workspace?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="aqaa-card p-6 gradient-mesh-blue">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">
          <Brain className="h-4 w-4 text-primary" aria-hidden="true" />
        </div>
        <p className="text-sm font-semibold text-foreground">Ask AQAA</p>
        <span className="ml-auto text-[11px] text-muted-foreground/60 font-medium">
          AI-powered quality intelligence
        </span>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="flex items-center gap-3 rounded-xl border border-border/80 bg-background/60 px-4 py-3 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
          <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your institution's quality and compliance…"
            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 outline-none"
            aria-label="Ask AQAA"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className={cn(
              "flex-shrink-0 flex items-center justify-center h-7 w-7 rounded-lg transition-all",
              query.trim()
                ? "bg-primary text-white hover:bg-primary/90 shadow-sm shadow-primary/25"
                : "bg-muted text-muted-foreground/40 cursor-not-allowed"
            )}
            aria-label="Submit question"
          >
            <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </form>

      <div className="mt-3 flex flex-wrap gap-2">
        {prompts.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => router.push(`/ai-workspace?q=${encodeURIComponent(p)}`)}
            className="text-[11.5px] text-muted-foreground hover:text-foreground bg-muted/50 hover:bg-muted rounded-lg px-2.5 py-1 transition-colors truncate max-w-[280px]"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Quick actions ─────────────────────────────────────────────────────────────

interface QuickAction {
  label: string;
  description: string;
  href: string;
  icon: React.ElementType;
  color: string;
  roles?: UserRole[];
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    label: "Audit Centre",
    description: "Run AI audits",
    href: "/audits",
    icon: Play,
    color: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50",
    roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"],
  },
  {
    label: "Upload Evidence",
    description: "Add documents",
    href: "/files/upload",
    icon: Upload,
    color: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"],
  },
  {
    label: "Knowledge Base",
    description: "Explore knowledge",
    href: "/knowledge/foundation",
    icon: BookOpen,
    color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50",
    roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"],
  },
  {
    label: "Upload Evidence",
    description: "Add documents",
    href: "/files/upload",
    icon: Upload,
    color: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    roles: ["lecturer"],
  },
  {
    label: "AI Workspace",
    description: "Intelligent conversations",
    href: "/ai-workspace",
    icon: Brain,
    color: "text-primary bg-primary/10",
    roles: ["lecturer"],
  },
  {
    label: "Quality Centre",
    description: "Evidence & findings",
    href: "/quality",
    icon: ShieldCheck,
    color: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
    roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"],
  },
  {
    label: "Reports",
    description: "Compliance reports",
    href: "/reports/compliance",
    icon: FileBarChart2,
    color: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50",
    roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department"],
  },
  {
    label: "AI Workspace",
    description: "Intelligent conversations",
    href: "/ai-workspace",
    icon: Brain,
    color: "text-primary bg-primary/10",
    roles: ["student"],
  },
  {
    label: "Programmes",
    description: "Browse programmes",
    href: "/programmes",
    icon: GraduationCap,
    color: "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50",
    roles: ["student"],
  },
  {
    label: "Institutions",
    description: "Manage institutions",
    href: "/institutions",
    icon: Building2,
    color: "text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50",
    roles: ["system_admin"],
  },
  {
    label: "Users",
    description: "Manage users",
    href: "/users",
    icon: Users,
    color: "text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-950/50",
    roles: ["system_admin"],
  },
  {
    label: "AI Providers",
    description: "Provider config",
    href: "/settings/ai-providers",
    icon: Cpu,
    color: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    roles: ["system_admin"],
  },
];

function QuickActions({ role }: { role?: UserRole }) {
  const visible = QUICK_ACTIONS.filter(
    (a) => !a.roles || !role || a.roles.includes(role)
  );
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {visible.map((action) => {
        const Icon = action.icon;
        return (
          <Link
            key={action.href}
            href={action.href}
            className="aqaa-card group flex flex-col items-start gap-2.5 p-4 hover:border-primary/30"
          >
            <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", action.color)}>
              <Icon className="h-4 w-4" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground leading-tight">{action.label}</p>
              <p className="text-[11.5px] text-muted-foreground mt-0.5">{action.description}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

// ── Activity feed item ────────────────────────────────────────────────────────

function ActivityItem({
  icon: Icon,
  color,
  label,
  time,
  href,
}: {
  icon: React.ElementType;
  color: string;
  label: string;
  time: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors group rounded-lg"
    >
      <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0", color)}>
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      </div>
      <p className="flex-1 text-sm text-foreground group-hover:text-foreground/80 truncate">
        {label}
      </p>
      <span className="text-xs text-muted-foreground flex-shrink-0 flex items-center gap-1">
        <Clock className="h-3 w-3" aria-hidden="true" />
        {time}
      </span>
      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 flex-shrink-0 group-hover:text-muted-foreground transition-colors" aria-hidden="true" />
    </Link>
  );
}

// ── Health stat tile ──────────────────────────────────────────────────────────

function StatTile({
  label,
  value,
  trend,
  icon: Icon,
  iconColor,
}: {
  label: string;
  value: string | number;
  trend?: string;
  icon: React.ElementType;
  iconColor: string;
}) {
  return (
    <div className="aqaa-card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</p>
        <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center", iconColor)}>
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        </div>
      </div>
      <p className="text-2xl font-bold text-foreground tabular-nums">{value}</p>
      {trend && (
        <p className="text-[11.5px] text-muted-foreground flex items-center gap-1">
          <TrendingUp className="h-3 w-3 text-emerald-500" aria-hidden="true" />
          {trend}
        </p>
      )}
    </div>
  );
}

// ── Role-specific "Continue Working" cards ────────────────────────────────────

interface WorkCard {
  label: string;
  description: string;
  href: string;
  icon: React.ElementType;
  tag: string;
}

function getContinueCards(role?: UserRole): WorkCard[] {
  if (role === "system_admin") {
    return [
      { label: "Institution Overview", description: "Review compliance scores and health metrics across all institutions", href: "/institutions", icon: Building2, tag: "Admin" },
      { label: "User Management", description: "Manage users, roles, and access permissions", href: "/users", icon: Users, tag: "Admin" },
      { label: "AI Workspace", description: "Cross-institution analysis and strategic intelligence", href: "/ai-workspace", icon: Brain, tag: "AI" },
    ];
  }
  if (role === "student") {
    return [
      { label: "Browse Programmes", description: "Explore academic programmes and their requirements", href: "/programmes", icon: GraduationCap, tag: "Academic" },
      { label: "Knowledge Base", description: "Access institutional policies and academic resources", href: "/knowledge/foundation", icon: BookOpen, tag: "Knowledge" },
      { label: "Ask AQAA", description: "Get AI-powered answers about your academic journey", href: "/ai-workspace", icon: Brain, tag: "AI" },
    ];
  }
  if (role === "quality_assurance_officer") {
    return [
      { label: "Extraction Review", description: "17 candidates awaiting review from knowledge extraction", href: "/knowledge/acquisition/extraction", icon: BookOpen, tag: "Knowledge" },
      { label: "Module Audit — ELE301", description: "Assessment compliance audit completed, 4 findings generated", href: "/audits", icon: ShieldCheck, tag: "Quality" },
      { label: "AI Workspace", description: "Accreditation readiness analysis for Faculty of Engineering", href: "/ai-workspace", icon: Brain, tag: "AI" },
    ];
  }
  if (role === "lecturer") {
    return [
      { label: "Upload Evidence", description: "Add module evidence before the next audit cycle", href: "/files/upload", icon: Upload, tag: "Quality" },
      { label: "Knowledge Base", description: "Access institutional policies and module resources", href: "/knowledge/foundation", icon: BookOpen, tag: "Knowledge" },
      { label: "AI Workspace", description: "Ask questions about your modules, compliance, and policies", href: "/ai-workspace", icon: Brain, tag: "AI" },
    ];
  }
  // coordinator / HOD / dean
  return [
    { label: "Upload Evidence", description: "Add module evidence before the next audit cycle", href: "/files/upload", icon: Upload, tag: "Quality" },
    { label: "Audit Centre", description: "Run or review AI-powered compliance audits", href: "/audits", icon: ShieldCheck, tag: "Quality" },
    { label: "AI Workspace", description: "Analyse compliance, findings, and accreditation readiness", href: "/ai-workspace", icon: Brain, tag: "AI" },
  ];
}

// ── Student home panel ────────────────────────────────────────────────────────

function StudentHomePanel() {
  return (
    <div className="aqaa-card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-4 border-b border-border/60">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-primary" aria-hidden="true" />
          Getting Started
        </h2>
      </div>
      <div className="divide-y divide-border/40">
        <ActivityItem
          icon={Brain}
          color="text-primary bg-primary/10"
          label="Ask AQAA about your programme or academic policies"
          time="Now"
          href="/ai-workspace"
        />
        <ActivityItem
          icon={BookOpen}
          color="text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/50"
          label="Explore the institutional knowledge base"
          time="Available"
          href="/knowledge/foundation"
        />
        <ActivityItem
          icon={GraduationCap}
          color="text-indigo-600 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-950/50"
          label="Browse academic programmes and modules"
          time="Available"
          href="/programmes"
        />
      </div>
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────

const DashboardViewInner = memo(function DashboardViewInner() {
  const { data } = useDashboardSummary();
  const { isCoordinator, isQAOfficer, isSysAdmin, isStudent } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: institutions } = useInstitutions();
  const userInstitution = institutions?.find((i) => i.id === user?.institution_id);
  const role = user?.role as UserRole | undefined;
  const firstName = user?.full_name?.split(" ")[0] ?? "there";
  const isSystemAdmin = role === "system_admin";

  const institutionLabel = isSystemAdmin
    ? "All Institutions"
    : userInstitution?.name ?? "AQAA Platform";

  const continueCards = getContinueCards(role);

  return (
    <div className="space-y-8 max-w-[1200px]">
      {/* ── Greeting header ──────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
            <span className="text-xs font-semibold text-primary uppercase tracking-widest">
              {getGreeting()}
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {firstName}
          </h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className="status-pill bg-primary/6 text-primary border-primary/20">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
              {institutionLabel}
            </span>
            {role && (
              <span className="status-pill bg-muted text-muted-foreground border-border/60">
                {ROLE_LABELS[role]}
              </span>
            )}
          </div>
        </div>

        {/* Health score — QA and admin only */}
        {(isQAOfficer || isSysAdmin) && (
          <div className="flex-shrink-0 aqaa-card px-5 py-4 flex flex-col items-center gap-1">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">87</div>
            <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Health</div>
            <div className="flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
              Good standing
            </div>
          </div>
        )}
      </div>

      {/* ── Ask AQAA composer — all roles ────────────────────────────────── */}
      <AskAQAAComposer role={role} />

      {/* ── Quick actions ────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground">Quick Actions</h2>
        </div>
        <QuickActions role={role} />
      </div>

      {/* ── Stats row (QA officer) ───────────────────────────────────────── */}
      {isQAOfficer && !isSysAdmin && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatTile
            label="Modules"
            value={data?.modules ?? "—"}
            trend="Across all programmes"
            icon={BookOpen}
            iconColor="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50"
          />
          <StatTile
            label="Programmes"
            value={data?.programmes ?? "—"}
            trend="Active"
            icon={Sparkles}
            iconColor="text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50"
          />
          <StatTile
            label="Open Findings"
            value={7}
            trend="3 critical"
            icon={AlertCircle}
            iconColor="text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50"
          />
          <StatTile
            label="Evidence Files"
            value="—"
            trend="Ready for audit"
            icon={ShieldCheck}
            iconColor="text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50"
          />
        </div>
      )}

      {/* ── Admin stats ──────────────────────────────────────────────────── */}
      {isSysAdmin && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatTile
            label="Institutions"
            value={institutions?.length ?? "—"}
            trend="Active tenants"
            icon={Building2}
            iconColor="text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50"
          />
          <StatTile
            label="Modules"
            value={data?.modules ?? "—"}
            trend="Across all institutions"
            icon={BookOpen}
            iconColor="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50"
          />
          <StatTile
            label="Programmes"
            value={data?.programmes ?? "—"}
            trend="All institutions"
            icon={Sparkles}
            iconColor="text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50"
          />
          <StatTile
            label="Open Findings"
            value={7}
            trend="Cross-institution"
            icon={AlertCircle}
            iconColor="text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50"
          />
        </div>
      )}

      {/* ── Recent AI activity + Today's priorities (coordinator+, not student) */}
      {isCoordinator && !isStudent && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="aqaa-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-4 border-b border-border/60">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Brain className="h-4 w-4 text-primary" aria-hidden="true" />
                Recent AI Activity
              </h2>
              <Link
                href="/ai-workspace"
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="h-3 w-3" aria-hidden="true" />
              </Link>
            </div>
            <div className="divide-y divide-border/40">
              <ActivityItem
                icon={CheckCircle2}
                color="text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/50"
                label="Module Folder Audit completed — ELE301"
                time="2h ago"
                href="/audits"
              />
              <ActivityItem
                icon={BookOpen}
                color="text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/50"
                label="Knowledge extraction: TUT website (23 candidates)"
                time="4h ago"
                href="/knowledge/acquisition/extraction"
              />
              <ActivityItem
                icon={AlertCircle}
                color="text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/50"
                label="3 findings require review in Faculty of Engineering"
                time="Yesterday"
                href="/findings"
              />
              <ActivityItem
                icon={ShieldCheck}
                color="text-violet-600 bg-violet-50 dark:text-violet-400 dark:bg-violet-950/50"
                label="Evidence verified: Assessment Compliance audit"
                time="2 days ago"
                href="/audits"
              />
            </div>
          </div>

          <div className="aqaa-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-4 border-b border-border/60">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-500" aria-hidden="true" />
                Today&apos;s Priorities
              </h2>
              <span className="text-[11px] text-muted-foreground">3 pending</span>
            </div>
            <div className="divide-y divide-border/40">
              <ActivityItem
                icon={Play}
                color="text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/50"
                label="Run Assessment Compliance audit — CSC401"
                time="Overdue"
                href="/audits"
              />
              <ActivityItem
                icon={Upload}
                color="text-violet-600 bg-violet-50 dark:text-violet-400 dark:bg-violet-950/50"
                label="Upload evidence folder for Moderation Review"
                time="Due today"
                href="/files/upload"
              />
              <ActivityItem
                icon={FileBarChart2}
                color="text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/50"
                label="Generate Q2 Compliance Report for Dean's review"
                time="Due Friday"
                href="/reports/compliance"
              />
              <ActivityItem
                icon={AlertCircle}
                color="text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/50"
                label="2 audit findings await your response"
                time="Due this week"
                href="/findings"
              />
            </div>
          </div>
        </div>
      )}

      {/* ── Student-specific panel ────────────────────────────────────────── */}
      {isStudent && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <StudentHomePanel />
          <div className="aqaa-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-4 border-b border-border/60">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
                About AQAA
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <p className="text-sm text-muted-foreground leading-relaxed">
                AQAA is your institution&apos;s Academic Quality Assurance platform. It ensures programmes, modules, and assessments meet national quality standards.
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Use the <strong className="text-foreground">AI Workspace</strong> to ask questions about your institution, programmes, and academic policies.
              </p>
              <Link
                href="/ai-workspace"
                className="inline-flex items-center gap-2 mt-2 text-sm font-medium text-primary hover:underline"
              >
                Open AI Workspace <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* ── Continue working ─────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground">Continue Working</h2>
          {!isStudent && (
            <Link href="/workspace" className="text-xs text-primary hover:underline flex items-center gap-1">
              Open Workspace <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {continueCards.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="aqaa-card group p-4 flex flex-col gap-3 hover:border-primary/30"
              >
                <div className="flex items-center justify-between">
                  <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
                  <span className="text-[10.5px] font-medium text-muted-foreground px-2 py-0.5 bg-muted rounded-full">
                    {item.tag}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{item.label}</p>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{item.description}</p>
                </div>
                <div className="flex items-center gap-1 text-xs text-primary font-medium mt-auto group-hover:gap-2 transition-all">
                  Continue <ArrowRight className="h-3 w-3" aria-hidden="true" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
});

export function DashboardView() {
  return <DashboardViewInner />;
}
