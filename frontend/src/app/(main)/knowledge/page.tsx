"use client";

import Link from "next/link";
import {
  Database,
  Download,
  ClipboardList,
  SearchCheck,
  GitBranch,
  FileText,
  ArrowRight,
  BookOpen,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

const STAFF: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"];
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
    label: "Knowledge Foundation",
    description: "Institutional knowledge coverage and data provenance across all entities",
    href: "/knowledge/foundation",
    icon: Database,
    iconColor: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50",
    badge: "Foundation",
    roles: STAFF,
  },
  {
    label: "Public Acquisition",
    description: "Register and crawl official public institutional sources with robots.txt compliance",
    href: "/knowledge/acquisition",
    icon: Download,
    iconColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50",
    badge: "Acquisition",
    roles: QA_AND_ABOVE,
  },
  {
    label: "Extraction Review",
    description: "Review and approve intelligently extracted academic metadata and entity mappings",
    href: "/knowledge/acquisition/extraction",
    icon: ClipboardList,
    iconColor: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
    badge: "AI",
    roles: QA_AND_ABOVE,
  },
  {
    label: "Semantic Search",
    description: "Search institutional knowledge and policies using AI-powered semantic retrieval",
    href: "/knowledge-search",
    icon: SearchCheck,
    iconColor: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
    badge: "RAG",
    roles: STAFF,
  },
  {
    label: "Knowledge Graph",
    description: "Explore connections between entities, policies, modules and programmes",
    href: "/ikp-management",
    icon: GitBranch,
    iconColor: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50",
    badge: "Graph",
    roles: QA_AND_ABOVE,
  },
  {
    label: "Documents",
    description: "Browse all institutional documents, policies and uploaded evidence files",
    href: "/files",
    icon: FileText,
    iconColor: "text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50",
    badge: "Library",
    roles: STAFF,
  },
];

export default function KnowledgeWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));

  return (
    <div className="max-w-[1100px] space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-primary/8 flex items-center justify-center flex-shrink-0">
          <BookOpen className="h-5 w-5 text-primary" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Knowledge</h1>
          <p className="text-muted-foreground mt-1 text-sm leading-relaxed">
            Institutional knowledge foundation, acquisition, extraction and semantic search.
          </p>
        </div>
      </div>

      {/* Card grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href}
              href={card.href}
              className="aqaa-card group flex flex-col gap-4 p-6 hover:border-primary/25 hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className={cn("w-9 h-9 rounded-xl flex items-center justify-center", card.iconColor)}>
                  <Icon className="h-4.5 w-4.5" aria-hidden="true" />
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
