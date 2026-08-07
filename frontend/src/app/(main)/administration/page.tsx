"use client";

import Link from "next/link";
import {
  Building2,
  Users,
  Shield,
  ShieldCheck,
  Brain,
  Activity,
  CalendarDays,
  FileText,
  Settings2,
  ArrowRight,
  Globe,
  Mail,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

const SA_ONLY: UserRole[] = ["system_admin"];
const ADMIN_AND_SA: UserRole[] = ["system_admin", "institution_admin"];

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
    label: "Invitations",
    description: "Create and manage secure one-time registration tokens for staff, students and external users",
    href: "/administration/invitations",
    icon: Mail,
    iconColor: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
    badge: "Onboarding",
    roles: ADMIN_AND_SA,
  },
  {
    label: "Domains",
    description: "Map institutional email domains and configure automatic student assignment rules",
    href: "/administration/domains",
    icon: Globe,
    iconColor: "text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50",
    badge: "Email",
    roles: ADMIN_AND_SA,
  },
  {
    label: "Institutions",
    description: "Manage institution records, codes, types, and hierarchy configurations",
    href: "/institutions",
    icon: Building2,
    iconColor: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50",
    badge: "Hierarchy",
    roles: SA_ONLY,
  },
  {
    label: "Users",
    description: "User accounts, roles, institution assignments and access management",
    href: "/users",
    icon: Users,
    iconColor: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    badge: "IAM",
    roles: SA_ONLY,
  },
  {
    label: "Roles",
    description: "Role definitions and permission boundary management across the platform",
    href: "/users",
    icon: Shield,
    iconColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50",
    badge: "RBAC",
    roles: SA_ONLY,
  },
  {
    label: "Permissions",
    description: "Fine-grained access controls and route permission configurations",
    href: "/settings/system",
    icon: ShieldCheck,
    iconColor: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
    badge: "Access",
    roles: SA_ONLY,
  },
  {
    label: "AI Providers",
    description: "Configure AI provider endpoints, API keys, and health monitoring",
    href: "/settings/ai-providers",
    icon: Brain,
    iconColor: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50",
    badge: "LLM",
    roles: SA_ONLY,
  },
  {
    label: "Monitoring",
    description: "Platform health, API performance, and system resource monitoring",
    href: "/settings/system",
    icon: Activity,
    iconColor: "text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50",
    badge: "Ops",
    roles: SA_ONLY,
  },
  {
    label: "Scheduler",
    description: "Scheduled jobs, automated audit triggers and maintenance windows",
    href: "/settings/system",
    icon: CalendarDays,
    iconColor: "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50",
    badge: "CRON",
    roles: SA_ONLY,
  },
  {
    label: "Logs",
    description: "Audit trail, system event logs and user activity reporting",
    href: "/settings/system",
    icon: FileText,
    iconColor: "text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50",
    badge: "Audit",
    roles: SA_ONLY,
  },
  {
    label: "Settings",
    description: "Global platform configuration, feature flags and environment settings",
    href: "/settings/system",
    icon: Settings2,
    iconColor: "text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-950/50",
    badge: "Config",
    roles: SA_ONLY,
  },
];

export default function AdministrationWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));

  return (
    <div className="max-w-[1100px] space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-900/60 flex items-center justify-center flex-shrink-0">
          <Settings2 className="h-5 w-5 text-gray-600 dark:text-gray-400" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Administration</h1>
          <p className="text-muted-foreground mt-1 text-sm leading-relaxed">
            Platform administration, users, AI providers, monitoring and system configuration.
          </p>
        </div>
      </div>

      {/* Card grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
