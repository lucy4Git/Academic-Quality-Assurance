"use client";

import { memo } from "react";
import {
  X, BookOpen, Brain, ArrowRight, CheckCircle2, Building2,
  FileText, Shield, Zap, BarChart2, TrendingUp, AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Citation } from "@/lib/api/ai-assistant";
import type { StreamSource } from "@/lib/api/ai-assistant";

const AGENT_ICONS: Record<string, React.ElementType> = {
  assessment: BarChart2,
  moderation: Shield,
  attendance: TrendingUp,
  evidence: BookOpen,
  outcome: Brain,
  accreditation: Shield,
  programme: FileText,
  qualification: Brain,
  knowledge: BookOpen,
  reporting: BarChart2,
  qa_assistant: Brain,
};

const ENTITY_DOTS: Record<string, string> = {
  policy: "bg-violet-500",
  document: "bg-blue-500",
  module: "bg-emerald-500",
  programme: "bg-indigo-500",
  qualification: "bg-amber-500",
  institution: "bg-rose-500",
  default: "bg-slate-400",
};

// ── Grounding gauge ───────────────────────────────────────────────────────────

function GroundingGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "text-emerald-500" : pct >= 50 ? "text-amber-500" : "text-rose-500";
  const trackColor =
    pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-rose-500";
  const label =
    pct >= 80 ? "Grounded" : pct >= 50 ? "Partial" : "Low confidence";

  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - pct / 100);

  return (
    <div className="flex items-center gap-3">
      {/* SVG donut */}
      <div className="relative w-16 h-16 flex-shrink-0">
        <svg viewBox="0 0 70 70" className="w-full h-full -rotate-90">
          <circle cx="35" cy="35" r={radius} fill="none" stroke="currentColor" strokeWidth="6" className="text-muted/30" />
          <circle
            cx="35" cy="35" r={radius}
            fill="none"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className={trackColor.replace("bg-", "stroke-")}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-[15px] font-bold leading-none", color)}>{pct}</span>
          <span className="text-[8px] text-muted-foreground leading-none mt-0.5">%</span>
        </div>
      </div>
      <div>
        <p className={cn("text-xs font-semibold", color)}>{label}</p>
        <p className="text-[10px] text-muted-foreground leading-snug mt-0.5">
          Knowledge grounding score for this response
        </p>
      </div>
    </div>
  );
}

// ── Source item ───────────────────────────────────────────────────────────────

function SourceItem({ source, index }: { source: StreamSource; index: number }) {
  const dot = ENTITY_DOTS[source.entity_type?.toLowerCase() ?? ""] ?? ENTITY_DOTS.default;
  const confidence = Math.round((source.confidence_score ?? source.relevance_score ?? 0) * 100);

  return (
    <div className="flex items-start gap-2.5 py-2 border-b border-border/50 last:border-0">
      <div className={cn("w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0", dot)} />
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-medium text-foreground leading-snug line-clamp-2">
          {source.title ?? source.entity_key ?? "Knowledge source"}
        </p>
        <div className="flex items-center gap-2 mt-1">
          {source.entity_type && (
            <span className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
              {source.entity_type}
            </span>
          )}
          {confidence > 0 && (
            <span className="text-[9px] text-muted-foreground/60">{confidence}%</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Citation item ─────────────────────────────────────────────────────────────

function CitationItem({ citation, index }: { citation: Citation; index: number }) {
  return (
    <div className="flex items-start gap-2.5 py-2 border-b border-border/50 last:border-0">
      <span className="w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-[9px] font-bold text-blue-700 dark:text-blue-300 flex-shrink-0 mt-0.5">
        {index + 1}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-medium text-foreground leading-snug line-clamp-2">
          {citation.title}
        </p>
        {citation.snippet && (
          <p className="text-[10px] text-muted-foreground leading-snug mt-0.5 line-clamp-2">
            {citation.snippet}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
            {citation.entity_type}
          </span>
          <span className="text-[9px] text-muted-foreground/60">
            {Math.round((citation.relevance_score ?? 0) * 100)}% relevant
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main context panel ────────────────────────────────────────────────────────

interface ContextPanelProps {
  institutionCode: string;
  groundingScore?: number;
  groundingStatus?: "grounded" | "partially_grounded" | "no_source_found";
  sources: StreamSource[];
  citations: Citation[];
  agents: string[];
  nextActions: string[];
  onActionClick: (action: string, route?: string) => void;
  onClose: () => void;
  messageCount: number;
}

const ACTION_ROUTES: Record<string, string> = {
  "Create audit": "/audits",
  "Generate report": "/reports",
  "Upload missing evidence": "/files/upload",
  "Open module workspace": "/workspace",
  "Search related policies": "/knowledge-search",
  "Start accreditation review": "/accreditation",
  "View findings": "/findings",
  "Open knowledge search": "/knowledge-search",
};

export const ContextPanel = memo(function ContextPanel({
  institutionCode,
  groundingScore,
  groundingStatus,
  sources,
  citations,
  agents,
  nextActions,
  onActionClick,
  onClose,
  messageCount,
}: ContextPanelProps) {
  const hasContent = sources.length > 0 || citations.length > 0 || agents.length > 0;

  const displayActions = nextActions.length > 0
    ? nextActions.slice(0, 5)
    : ["Create audit", "Generate report", "Upload missing evidence", "Search related policies"];

  return (
    <div className="w-[280px] shrink-0 flex flex-col border-l border-border bg-sidebar overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div>
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Live Context
          </span>
          {institutionCode && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <Building2 className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium text-foreground">{institutionCode}</span>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Close context panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Grounding score */}
        {groundingScore !== undefined && (
          <div className="px-4 py-4 border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
              Grounding Score
            </p>
            <GroundingGauge score={groundingScore} />
            {groundingStatus === "no_source_found" && (
              <div className="flex items-center gap-1.5 mt-2 text-amber-600 dark:text-amber-400">
                <AlertCircle className="h-3 w-3" />
                <span className="text-[10px]">No institutional sources found</span>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!hasContent && messageCount === 0 && (
          <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
            <Zap className="h-7 w-7 text-muted-foreground/20 mb-2" />
            <p className="text-xs text-muted-foreground">Context loads after your first query</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5 leading-snug">
              Sources, agents and actions will appear here
            </p>
          </div>
        )}

        {/* Knowledge citations */}
        {citations.length > 0 && (
          <div className="px-4 py-3 border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
              Citations ({citations.length})
            </p>
            <div>
              {citations.slice(0, 6).map((c, i) => (
                <CitationItem key={c.source_id ?? i} citation={c} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* Knowledge sources */}
        {sources.length > 0 && (
          <div className="px-4 py-3 border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
              Knowledge Sources ({sources.length})
            </p>
            <div>
              {sources.slice(0, 5).map((s, i) => (
                <SourceItem key={i} source={s} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* Agents used */}
        {agents.length > 0 && (
          <div className="px-4 py-3 border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
              Agents
            </p>
            <div className="space-y-1.5">
              {agents.map((agent) => {
                const Icon = AGENT_ICONS[agent] ?? Brain;
                return (
                  <div
                    key={agent}
                    className="flex items-center gap-2 rounded-lg bg-muted/60 px-2.5 py-1.5"
                  >
                    <Icon className="h-3 w-3 text-blue-500 flex-shrink-0" />
                    <span className="text-[11px] font-medium text-foreground capitalize">
                      {agent.replace(/_/g, " ")}
                    </span>
                    <CheckCircle2 className="h-3 w-3 text-emerald-500 ml-auto" />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Suggested actions */}
        <div className="px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
            Next Actions
          </p>
          <div className="space-y-1">
            {displayActions.map((action, i) => {
              const route = ACTION_ROUTES[action];
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => onActionClick(action, route)}
                  className="w-full flex items-center gap-2 rounded-lg border border-border bg-card px-2.5 py-2 text-left hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/30 transition-colors group"
                >
                  <ArrowRight className="h-3 w-3 text-muted-foreground group-hover:text-blue-500 flex-shrink-0 transition-colors" />
                  <span className="text-[11px] text-foreground group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors truncate">
                    {action}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
});
