"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Brain,
  BrainCircuit,
  Calculator,
  ArrowRight,
  FileText,
  Search,
  Star,
  Clock,
  Zap,
  Sparkles,
  ChevronRight,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Suggested prompts ────────────────────────────────────────────────────────

const PROMPTS = [
  { category: "Quality",      icon: "✅", prompt: "What are the top audit findings across all modules this semester?" },
  { category: "Knowledge",    icon: "📚", prompt: "Summarise the institutional knowledge gaps from the latest extraction run" },
  { category: "Accreditation", icon: "🎓", prompt: "Is the Faculty of Engineering ready for CHE accreditation?" },
  { category: "Compliance",   icon: "📋", prompt: "Generate a compliance summary for all active programmes" },
  { category: "Research",     icon: "🔬", prompt: "Compare NQF levels and credits across Computer Science modules" },
  { category: "Governance",   icon: "🏛️", prompt: "What policy documents need to be updated before the next audit cycle?" },
];

// ── AI Tools ─────────────────────────────────────────────────────────────────

const AI_TOOLS = [
  {
    label: "AI QA Assistant",
    description: "Guided QA conversations with citation tracking",
    href: "/ai-assistant",
    icon: Brain,
    badge: "Core",
    iconClass: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50",
  },
  {
    label: "AI Workspace",
    description: "Open-ended analysis with deep knowledge access",
    href: "/ai-workspace",
    icon: BrainCircuit,
    badge: "Advanced",
    iconClass: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50",
  },
  {
    label: "Qualification Intelligence",
    description: "Programme quality scoring and NQF alignment",
    href: "/qualification-intelligence",
    icon: Calculator,
    badge: "Analysis",
    iconClass: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50",
  },
  {
    label: "Institution Workspace",
    description: "Institution-wide strategic AI planning",
    href: "/ai",
    icon: Building2,
    badge: "Strategic",
    iconClass: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50",
  },
];

// ── Recent sessions ───────────────────────────────────────────────────────────

const RECENT_SESSIONS = [
  {
    title: "Accreditation readiness — Faculty of Engineering",
    summary: "Analysed 12 programmes against CHE standards…",
    time: "2 hours ago",
    href: "/ai-workspace",
    icon: "🎓",
  },
  {
    title: "Module audit findings synthesis — CSC401",
    summary: "Summarised 7 assessment compliance findings…",
    time: "Yesterday",
    href: "/ai-workspace",
    icon: "📋",
  },
  {
    title: "NQF mapping — Computer Science programmes",
    summary: "Compared NQF 6–8 credit structures across 4 programmes…",
    time: "3 days ago",
    href: "/ai-workspace",
    icon: "📊",
  },
];

const PINNED_DOCS = [
  { label: "Assessment Policy 2026", href: "/files" },
  { label: "TUT Knowledge Foundation", href: "/knowledge/foundation" },
  { label: "Accreditation Checklist", href: "/files" },
];

// ── Component ────────────────────────────────────────────────────────────────

export function WorkspaceLandingView() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/ai-assistant?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="max-w-[1100px] space-y-10">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="text-center space-y-3 pt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/6 border border-primary/15 text-xs font-semibold text-primary mb-1">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          AI Workspace
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-foreground">
          What would you like to explore?
        </h1>
        <p className="text-base text-muted-foreground max-w-lg mx-auto leading-relaxed">
          Ask AQAA anything about your institution's quality, knowledge, compliance, and accreditation.
        </p>
      </div>

      {/* ── Ask AQAA input ────────────────────────────────────────────────── */}
      <form onSubmit={handleAsk} className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 rounded-2xl border-2 border-border bg-card px-5 py-4 shadow-sm focus-within:border-primary/40 focus-within:shadow-lg focus-within:shadow-primary/5 transition-all duration-200">
          <Brain className="h-5 w-5 text-primary flex-shrink-0" aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask AQAA anything…"
            className="flex-1 bg-transparent text-base text-foreground placeholder:text-muted-foreground/40 outline-none"
            aria-label="Ask AQAA"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            aria-label="Submit"
            className={cn(
              "flex-shrink-0 flex items-center justify-center h-9 w-9 rounded-xl transition-all duration-150",
              query.trim()
                ? "bg-primary text-white hover:bg-primary/90 shadow-md shadow-primary/25"
                : "bg-muted text-muted-foreground/30 cursor-not-allowed"
            )}
          >
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </form>

      {/* ── Suggested prompts ──────────────────────────────────────────────── */}
      <div className="max-w-2xl mx-auto">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 text-center">
          Suggested
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {PROMPTS.map((p) => (
            <button
              key={p.prompt}
              type="button"
              onClick={() => router.push(`/ai-assistant?q=${encodeURIComponent(p.prompt)}`)}
              className="flex items-start gap-2.5 p-3 rounded-xl border border-border/60 bg-card/50 hover:bg-card hover:border-border hover:shadow-sm text-left transition-all group cursor-pointer"
            >
              <span className="text-base leading-none mt-0.5 flex-shrink-0" aria-hidden="true">{p.icon}</span>
              <div className="min-w-0 flex-1">
                <span className="text-[10.5px] font-semibold text-primary uppercase tracking-wide block mb-0.5">
                  {p.category}
                </span>
                <p className="text-[12.5px] text-foreground/80 leading-snug line-clamp-2">{p.prompt}</p>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-muted-foreground flex-shrink-0 mt-1 ml-auto transition-colors" aria-hidden="true" />
            </button>
          ))}
        </div>
      </div>

      {/* ── AI Tools ──────────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-4 w-4 text-primary" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-foreground">AI Tools</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {AI_TOOLS.map((tool) => {
            const Icon = tool.icon;
            return (
              <Link
                key={tool.href}
                href={tool.href}
                className="aqaa-card group p-4 flex flex-col gap-3 hover:border-primary/30"
              >
                <div className="flex items-center justify-between">
                  <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", tool.iconClass)}>
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/60 px-2 py-0.5 bg-muted rounded-full">
                    {tool.badge}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{tool.label}</p>
                  <p className="text-[11.5px] text-muted-foreground mt-1 leading-snug">{tool.description}</p>
                </div>
                <div className="flex items-center gap-1 text-xs text-primary font-medium mt-auto group-hover:gap-2 transition-all">
                  Open <ArrowRight className="h-3 w-3" aria-hidden="true" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* ── Recent + Pinned ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent conversations */}
        <div className="lg:col-span-2 aqaa-card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border/60">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              Recent Conversations
            </h2>
            <Link href="/ai-workspace" className="text-xs text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </div>
          <div className="divide-y divide-border/40">
            {RECENT_SESSIONS.map((session) => (
              <Link
                key={session.title}
                href={session.href}
                className="flex items-start gap-3 px-5 py-3.5 hover:bg-muted/30 transition-colors group"
              >
                <span className="text-xl leading-none flex-shrink-0 mt-0.5" aria-hidden="true">{session.icon}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                    {session.title}
                  </p>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">{session.summary}</p>
                </div>
                <span className="text-[11px] text-muted-foreground/60 flex-shrink-0 mt-0.5 whitespace-nowrap">{session.time}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Pinned */}
        <div className="aqaa-card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border/60">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Star className="h-4 w-4 text-amber-500" aria-hidden="true" />
              Pinned
            </h2>
            <Link href="/files" className="text-xs text-primary hover:underline">Browse</Link>
          </div>
          <div className="divide-y divide-border/40">
            {PINNED_DOCS.map((doc) => (
              <Link
                key={doc.label}
                href={doc.href}
                className="flex items-center gap-3 px-5 py-3 hover:bg-muted/30 transition-colors group"
              >
                <FileText className="h-3.5 w-3.5 text-muted-foreground/60 flex-shrink-0" aria-hidden="true" />
                <p className="text-[12.5px] text-foreground truncate flex-1 group-hover:text-primary transition-colors">
                  {doc.label}
                </p>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 flex-shrink-0 group-hover:text-muted-foreground transition-colors" aria-hidden="true" />
              </Link>
            ))}
            <Link
              href="/knowledge-search"
              className="flex items-center gap-3 px-5 py-3 hover:bg-muted/30 transition-colors group"
            >
              <Search className="h-3.5 w-3.5 text-primary/60 flex-shrink-0" aria-hidden="true" />
              <p className="text-[12.5px] text-primary font-medium">Search knowledge base</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
