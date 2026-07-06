"use client";

import {
  useState, useRef, useEffect, useCallback, memo,
} from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useAuthStore } from "@/store/auth.store";
import {
  useAsk,
  useAgentRouter,
  useSuggestedPrompts,
  useCreateSession,
  useChatSessions,
  useDeleteSession,
  type AgentRouterResponse,
} from "@/hooks/useAiAssistant";
import { useMultiAgent, type MultiAgentResponse } from "@/hooks/useWorkspace";
import type { AskResponse, SourceChunk } from "@/types/ai-assistant";
import { askStream, type StreamSource } from "@/lib/api/ai-assistant";
import {
  Brain, Plus, Trash2, ChevronRight, Download, BookOpen, Zap, Shield,
  BarChart2, Search, GitBranch, GraduationCap, CheckSquare, Layers,
  Copy, Send, MessageSquare, Clock, Building2, X, PanelRightClose,
  PanelRightOpen, CheckCircle2, Loader2, ArrowRight, FileText, Upload,
  ClipboardCheck, RotateCcw, Star, ExternalLink, AlertCircle, Info,
  Sparkles, Hash,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Constants ────────────────────────────────────────────────────────────────

const ACTIVE_INSTITUTIONS = ["TUT", "UP"];

const AGENT_ICONS: Record<string, React.ElementType> = {
  assessment: CheckSquare,
  moderation: Shield,
  attendance: Layers,
  evidence: BookOpen,
  outcome: GraduationCap,
  accreditation: Shield,
  programme: GitBranch,
  qualification: GraduationCap,
  knowledge: Search,
  reporting: BarChart2,
  workflow: Zap,
  qa_assistant: Brain,
  qa_general: Brain,
};

const AGENT_COLOURS: Record<string, string> = {
  assessment:    "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-800",
  moderation:    "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300 dark:border-purple-800",
  evidence:      "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800",
  accreditation: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800",
  reporting:     "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800",
  qualification: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800",
  qa_assistant:  "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:border-slate-700",
};

const SLASH_COMMANDS = [
  { cmd: "/audit",         label: "Audit Query",        desc: "Analyse audit evidence", mode: "audit_summary" },
  { cmd: "/policy",        label: "Policy Search",       desc: "Search institution policy", mode: "qa_assistant" },
  { cmd: "/evidence",      label: "Evidence Check",      desc: "Check module evidence", mode: "evidence" },
  { cmd: "/report",        label: "Generate Report",     desc: "Create a QA report", mode: "reporting" },
  { cmd: "/qualification", label: "Qualification",       desc: "NQF/credit analysis", mode: "qualification" },
];

const ACTION_ROUTES: Record<string, string> = {
  "Create audit":              "/audits",
  "Generate report":           "/reports",
  "Upload missing evidence":   "/files/upload",
  "Open module workspace":     "/workspace",
  "Search related policies":   "/knowledge-search",
  "Start accreditation review":"/accreditation",
  "View findings":             "/findings",
  "Open knowledge search":     "/knowledge-search",
};

const THINKING_STEPS = [
  "Understanding request",
  "Searching institutional knowledge",
  "Consulting QA agents",
  "Checking evidence database",
  "Generating recommendation",
];

const EMPTY_PROMPTS = [
  { category: "Audit", label: "Review a module folder", prompt: "Review the evidence folder for CSC401 and identify compliance gaps." },
  { category: "Accreditation", label: "Accreditation readiness", prompt: "Generate an accreditation readiness report for the ICT faculty." },
  { category: "Evidence", label: "Find missing evidence", prompt: "Which modules are missing moderation reports this semester?" },
  { category: "Qualification", label: "Compare qualifications", prompt: "Compare the credit structure of BSc CS at TUT against NQF Level 7 requirements." },
  { category: "Policy", label: "Search institution policy", prompt: "What is the institutional policy on supplementary assessments?" },
  { category: "Reporting", label: "Programme quality summary", prompt: "Summarise the quality status of the IT programme for Senate." },
];

// ── Types ────────────────────────────────────────────────────────────────────

interface WorkspaceMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  isMultiAgent?: boolean;
  isStreaming?: boolean;
  confidence?: number;
  // SourceChunk (from /ask), string (from agent router), or StreamSource (from /ask-stream)
  // biome-ignore lint: intentional union — three source shapes from different endpoints
  sources?: unknown[];
  nextActions?: string[];
  followUps?: string[];
  provider?: string;
  model?: string;
  timestamp: Date;
  routerResult?: AgentRouterResponse;
  contributions?: { agent: string; confidence: number; summary?: string }[];
}

// ── Thinking animation ───────────────────────────────────────────────────────

function ThinkingAnimation({ isMultiAgent }: { isMultiAgent: boolean }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    setStep(0);
    const t = setInterval(() => setStep((s) => Math.min(s + 1, THINKING_STEPS.length - 1)), 1600);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-tl-sm border border-border bg-card px-5 py-4 shadow-sm max-w-md">
        <div className="flex items-center gap-2 mb-3">
          <div className="h-5 w-5 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
            <Brain className="h-3 w-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-indigo-600">
            {isMultiAgent ? "Orchestrating agents…" : "AQAA is analysing…"}
          </span>
        </div>
        <div className="space-y-2">
          {THINKING_STEPS.map((s, i) => (
            <motion.div
              key={s}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: i <= step ? 1 : 0.25, x: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className={cn("flex items-center gap-2 text-xs", i < step
                ? "text-muted-foreground"
                : i === step
                ? "text-indigo-600 font-medium"
                : "text-muted-foreground/40"
              )}
            >
              {i < step ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
              ) : i === step ? (
                <Loader2 className="h-3.5 w-3.5 text-indigo-500 animate-spin flex-shrink-0" />
              ) : (
                <div className="h-3.5 w-3.5 rounded-full border border-muted-foreground/20 flex-shrink-0" />
              )}
              {s}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Message bubble ───────────────────────────────────────────────────────────

const MessageBubble = memo(function MessageBubble({
  msg,
  onFollowUp,
  onExport,
  isLatest,
}: {
  msg: WorkspaceMessage;
  onFollowUp: (q: string) => void;
  onExport: (content: string) => void;
  isLatest: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copied to clipboard");
  };

  if (msg.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="flex justify-end"
      >
        <div className="max-w-[72%] group">
          <div className="rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-3 text-sm text-white shadow-sm">
            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
          </div>
          <div className="flex justify-end mt-1">
            <span className="text-[10px] text-muted-foreground">
              {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </div>
      </motion.div>
    );
  }

  const pct = msg.confidence !== undefined ? Math.round(msg.confidence * 100) : null;
  const confColour =
    pct === null ? "" : pct >= 70 ? "text-emerald-600" : pct >= 45 ? "text-amber-500" : "text-red-500";
  const barColour =
    pct === null ? "" : pct >= 70 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex justify-start"
    >
      <div className="max-w-[84%] space-y-2.5">
        {/* Agent badges */}
        {msg.agents && msg.agents.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {msg.agents.map((a) => {
              const Icon = AGENT_ICONS[a] ?? Brain;
              return (
                <span
                  key={a}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
                    AGENT_COLOURS[a] ?? AGENT_COLOURS["qa_assistant"]
                  )}
                >
                  <Icon className="h-3 w-3" />
                  {a.replace(/_/g, " ")}
                </span>
              );
            })}
            {msg.isMultiAgent && (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 border border-purple-200 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 dark:border-purple-800">
                <Zap className="h-3 w-3" />
                Multi-agent
              </span>
            )}
          </div>
        )}

        {/* Answer card */}
        <div className="rounded-2xl rounded-tl-sm border border-border bg-card px-5 py-4 shadow-sm">
          {/* AQAA header */}
          <div className="flex items-center gap-2 mb-3">
            <div className="h-5 w-5 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
              <Brain className="h-3 w-3 text-white" />
            </div>
            <span className="text-xs font-semibold text-foreground">AQAA</span>
            {msg.provider && (
              <span className="text-xs text-muted-foreground ml-auto">
                {msg.provider} · {msg.model}
              </span>
            )}
          </div>

          <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
            {msg.content}
            {msg.isStreaming && (
              <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 align-middle animate-pulse" />
            )}
          </p>

          {/* Confidence bar */}
          {pct !== null && (
            <div className="mt-3 flex items-center gap-2">
              <div className="h-1.5 w-28 rounded-full bg-muted overflow-hidden flex-shrink-0">
                <div className={cn("h-full rounded-full", barColour)} style={{ width: `${pct}%` }} />
              </div>
              <span className={cn("text-xs font-medium", confColour)}>{pct}% confidence</span>
            </div>
          )}

          {/* Sources (compact inline, full list in right panel) */}
          {msg.sources && msg.sources.length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                Sources ({msg.sources.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {msg.sources.slice(0, 4).map((s, i) => {
                  const obj = s as Record<string, unknown>;
                  const label = typeof s === "string" ? s : ((obj.title || obj.entity_key) as string | undefined);
                  const score = typeof s === "string" ? null : (obj.relevance_score as number | undefined);
                  return (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-md border border-blue-100 bg-blue-50 px-2 py-0.5 text-xs text-blue-700 dark:border-blue-900 dark:bg-blue-950/30 dark:text-blue-300"
                    >
                      <BookOpen className="h-2.5 w-2.5 flex-shrink-0" />
                      <span className="truncate max-w-[120px]">{label}</span>
                      {score != null && (
                        <span className="text-blue-400 ml-0.5">({(score * 100).toFixed(0)}%)</span>
                      )}
                    </span>
                  );
                })}
                {msg.sources.length > 4 && (
                  <span className="text-xs text-muted-foreground self-center">
                    +{msg.sources.length - 4} more in panel →
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="mt-3 pt-3 border-t border-border flex items-center gap-1.5">
            <button
              onClick={handleCopy}
              aria-label="Copy response"
              className="flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              {copied ? <CheckCircle2 className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              onClick={() => onExport(msg.content)}
              aria-label="Export response"
              className="flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <Download className="h-3 w-3" />
              Export
            </button>
            <span className="ml-auto text-[10px] text-muted-foreground">
              {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </div>

        {/* Multi-agent contribution cards */}
        {msg.isMultiAgent && msg.contributions && msg.contributions.length > 0 && (
          <div className="space-y-1.5 pl-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Agent contributions
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {msg.contributions.slice(0, 4).map((c, i) => {
                const Icon = AGENT_ICONS[c.agent] ?? Brain;
                const cpct = Math.round(c.confidence * 100);
                return (
                  <div
                    key={i}
                    className="rounded-xl border border-border bg-card px-3 py-2 flex items-center gap-2"
                  >
                    <Icon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[11px] font-medium text-foreground truncate capitalize">
                        {c.agent.replace(/_/g, " ")}
                      </p>
                      <p className={cn("text-[10px] font-semibold", cpct >= 70 ? "text-emerald-600" : cpct >= 45 ? "text-amber-500" : "text-red-500")}>
                        {cpct}%
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Follow-up questions */}
        {msg.followUps && msg.followUps.length > 0 && (
          <div className="space-y-1 pl-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Follow-up
            </p>
            <div className="flex flex-wrap gap-1.5">
              {msg.followUps.slice(0, 3).map((q, i) => (
                <button
                  key={i}
                  onClick={() => onFollowUp(q)}
                  className="rounded-full border border-border bg-background px-3 py-1 text-xs text-foreground hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/30 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
});

// ── Right panel (sources + agents + actions) ─────────────────────────────────

function SourceCard({ source, index }: { source: unknown; index: number }) {
  const router = useRouter();
  const obj = typeof source === "object" && source !== null ? source as Record<string, unknown> : null;
  const title = typeof source === "string" ? source : (obj?.title as string || obj?.entity_key as string || "Source");
  const entityType = typeof source === "string" ? "document" : ((obj?.entity_type as string) ?? "document");
  const snippet = typeof source === "string" ? null : (obj?.text as string ?? null);
  const score = typeof source === "string" ? null : (obj?.relevance_score as number ?? null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(typeof source === "string" ? source : (obj?.entity_key as string ?? title));
    toast.success("Citation copied");
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: index * 0.05 }}
      className="rounded-xl border border-border bg-card p-3 space-y-2"
    >
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 mt-0.5 h-7 w-7 rounded-lg bg-blue-50 dark:bg-blue-950/40 flex items-center justify-center">
          <FileText className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-foreground leading-tight truncate">{title}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[10px] text-muted-foreground capitalize">{entityType.replace(/_/g, " ")}</span>
            {score !== null && (
              <>
                <span className="text-muted-foreground/30">·</span>
                <span className={cn("text-[10px] font-semibold", score >= 0.7 ? "text-emerald-600" : score >= 0.45 ? "text-amber-500" : "text-red-500")}>
                  {(score * 100).toFixed(0)}% match
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {snippet && (
        <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3 pl-9">
          {snippet}
        </p>
      )}

      <div className="flex items-center gap-1 pl-9">
        <button
          onClick={() => router.push(`/knowledge-search?q=${encodeURIComponent(title)}`)}
          aria-label="Open in Knowledge Search"
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[10px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <Search className="h-2.5 w-2.5" />
          Search
        </button>
        <button
          onClick={handleCopy}
          aria-label="Copy citation"
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[10px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <Copy className="h-2.5 w-2.5" />
          Cite
        </button>
      </div>
    </motion.div>
  );
}

function RightPanel({
  message,
  onClose,
}: {
  message: WorkspaceMessage | null;
  onClose: () => void;
}) {
  const router = useRouter();

  const sources = message?.sources ?? [];
  const nextActions = message?.nextActions ?? [];
  const agents = message?.agents ?? [];

  return (
    <div className="w-72 shrink-0 flex flex-col border-l border-border bg-sidebar overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Sources & Context</span>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close right panel">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Sources */}
        {sources.length > 0 ? (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
              Source Documents ({sources.length})
            </p>
            {sources.map((s, i) => (
              <SourceCard key={i} source={s} index={i} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground/30 mb-2" />
            <p className="text-xs text-muted-foreground">No sources for this response</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5">Ask a question to see citations</p>
          </div>
        )}

        {/* Agents used */}
        {agents.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
              Agents Used
            </p>
            {agents.map((a) => {
              const Icon = AGENT_ICONS[a] ?? Brain;
              return (
                <div
                  key={a}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl border px-3 py-2",
                    AGENT_COLOURS[a] ?? AGENT_COLOURS["qa_assistant"]
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold capitalize">{a.replace(/_/g, " ")}</p>
                    <p className="text-[10px] opacity-70">Active</p>
                  </div>
                  <CheckCircle2 className="h-3.5 w-3.5 ml-auto opacity-70" />
                </div>
              );
            })}
          </div>
        )}

        {/* Suggested next actions */}
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
            Suggested Actions
          </p>
          {(nextActions.length > 0 ? nextActions : [
            "Create audit",
            "Generate report",
            "Upload missing evidence",
            "Search related policies",
          ]).slice(0, 5).map((action, i) => {
            const route = ACTION_ROUTES[action];
            return (
              <button
                key={i}
                onClick={() => route && router.push(route)}
                className="w-full flex items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2 text-left hover:border-indigo-400 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30 transition-colors group"
              >
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-indigo-500 flex-shrink-0 transition-colors" />
                <span className="text-xs text-foreground group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors truncate">
                  {action}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Left sidebar ─────────────────────────────────────────────────────────────

function LeftSidebar({
  activeSessionId,
  onSelect,
  onNew,
  onDelete,
  institutionCode,
  isAdmin,
  onInstitutionChange,
}: {
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  institutionCode: string;
  isAdmin: boolean;
  onInstitutionChange: (code: string) => void;
}) {
  const { data: sessions } = useChatSessions();

  return (
    <div className="w-64 shrink-0 flex flex-col border-r border-border bg-sidebar overflow-hidden">
      {/* New chat */}
      <div className="p-3 border-b border-border">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-500/20"
          aria-label="Start new conversation"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </button>
      </div>

      {/* Institution selector (admin only) */}
      {isAdmin && (
        <div className="px-3 py-2 border-b border-border">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 px-1">
            Institution context
          </p>
          <select
            value={institutionCode}
            onChange={(e) => onInstitutionChange(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-indigo-400"
            aria-label="Select institution"
          >
            <option value="">All institutions…</option>
            {ACTIVE_INSTITUTIONS.map((code) => (
              <option key={code} value={code}>{code}</option>
            ))}
          </select>
        </div>
      )}

      {/* Context badge (non-admin) */}
      {!isAdmin && institutionCode && (
        <div className="px-3 py-2 border-b border-border">
          <div className="flex items-center gap-2 rounded-lg bg-muted px-2.5 py-1.5">
            <Building2 className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
            <span className="text-xs font-medium text-foreground">{institutionCode}</span>
            <span className="text-[10px] text-muted-foreground ml-auto">Workspace</span>
          </div>
        </div>
      )}

      {/* Session history */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <p className="px-2 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Recent conversations
        </p>
        {!sessions || sessions.length === 0 ? (
          <div className="px-3 py-10 text-center">
            <MessageSquare className="h-8 w-8 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-xs text-muted-foreground">No conversations yet</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5">
              Start a new conversation above
            </p>
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              role="button"
              tabIndex={0}
              aria-label={`Open conversation: ${s.title || s.mode}`}
              onKeyDown={(e) => e.key === "Enter" && onSelect(s.id)}
              className={cn(
                "group flex items-center justify-between gap-2 rounded-xl px-3 py-2.5 cursor-pointer transition-colors",
                s.id === activeSessionId
                  ? "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-900 dark:text-indigo-100"
                  : "hover:bg-muted text-sidebar-foreground"
              )}
              onClick={() => onSelect(s.id)}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate">
                  {s.title || s.mode.replace(/_/g, " ")}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Clock className="h-2.5 w-2.5 text-muted-foreground opacity-60" />
                  <span className="text-[10px] text-muted-foreground">{s.message_count} messages</span>
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                aria-label="Delete conversation"
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all shrink-0"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Quick links */}
      <div className="p-3 border-t border-border space-y-0.5">
        <p className="px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1">
          Quick access
        </p>
        {[
          { label: "Knowledge Search", href: "/knowledge-search", icon: Search },
          { label: "File Library",     href: "/files",            icon: BookOpen },
          { label: "Audit Centre",     href: "/audits",           icon: CheckSquare },
          { label: "Reports",          href: "/reports",          icon: BarChart2 },
        ].map((link) => {
          const Icon = link.icon;
          return (
            <a
              key={link.href}
              href={link.href}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Icon className="h-3.5 w-3.5 flex-shrink-0" />
              {link.label}
              <ChevronRight className="h-3 w-3 ml-auto opacity-40" />
            </a>
          );
        })}
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState({
  onSubmit,
  suggestedData,
}: {
  onSubmit: (q: string) => void;
  suggestedData?: { prompts: { prompt: string; category: string }[] } | null;
}) {
  const prompts = suggestedData && suggestedData.prompts.length > 0
    ? suggestedData.prompts.slice(0, 6).map((p) => ({
        category: p.category,
        label: p.prompt.slice(0, 40) + (p.prompt.length > 40 ? "…" : ""),
        prompt: p.prompt,
      }))
    : EMPTY_PROMPTS;

  return (
    <div className="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto px-4">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600 mb-5 shadow-lg shadow-indigo-500/25"
      >
        <Brain className="h-8 w-8 text-white" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <h2 className="text-2xl font-bold text-foreground mb-2">Ask AQAA</h2>
        <p className="text-sm text-muted-foreground leading-relaxed mb-1">
          Ask anything about academic quality assurance.
        </p>
        <p className="text-xs text-muted-foreground/60 mb-7">
          AQAA automatically routes your question to the right specialist agent.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.18 }}
        className="w-full"
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Try asking…
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {prompts.map((p, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.22 + i * 0.05 }}
              whileHover={{ y: -2 }}
              onClick={() => onSubmit(p.prompt)}
              className="rounded-xl border border-border bg-card px-4 py-3 text-left hover:border-indigo-400 hover:shadow-md transition-all group"
            >
              <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5 group-hover:text-indigo-500 transition-colors">
                {p.category}
              </span>
              <span className="text-xs text-foreground leading-snug">{p.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// ── Prompt composer ───────────────────────────────────────────────────────────

function PromptComposer({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled,
  useMultiAgentMode,
  onToggleMultiAgent,
  institutionCode,
  isAdmin,
  messageCount,
  onClear,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (q: string) => void;
  isLoading: boolean;
  disabled: boolean;
  useMultiAgentMode: boolean;
  onToggleMultiAgent: () => void;
  institutionCode: string;
  isAdmin: boolean;
  messageCount: number;
  onClear: () => void;
}) {
  const [showSlash, setShowSlash] = useState(false);
  const [slashFilter, setSlashFilter] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const v = e.target.value;
    onChange(v);
    // Auto-resize
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
    // Slash menu
    const lastWord = v.split(/\s/).pop() ?? "";
    if (lastWord.startsWith("/")) {
      setSlashFilter(lastWord.slice(1).toLowerCase());
      setShowSlash(true);
    } else {
      setShowSlash(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Escape") { setShowSlash(false); return; }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!showSlash) onSubmit(value);
    }
  };

  const applySlash = (cmd: { cmd: string; label: string }) => {
    const parts = value.split(/\s/);
    parts.pop();
    onChange(parts.join(" ") + (parts.length ? " " : "") + cmd.label + ": ");
    setShowSlash(false);
    textareaRef.current?.focus();
  };

  const filteredCommands = SLASH_COMMANDS.filter(
    (c) => c.cmd.slice(1).includes(slashFilter) || c.label.toLowerCase().includes(slashFilter)
  );

  const placeholder =
    isAdmin && !institutionCode
      ? "Select an institution to start…"
      : "Ask about audits, evidence, policies, qualifications, or reports…  (/ for commands)";

  return (
    <div className="border-t border-border bg-background px-4 py-3">
      {/* Session meta row */}
      {messageCount > 0 && (
        <div className="flex items-center justify-between mb-2 px-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <MessageSquare className="h-3 w-3" />
            <span>{messageCount} messages</span>
            {institutionCode && (
              <>
                <span className="text-muted-foreground/30">·</span>
                <Building2 className="h-3 w-3" />
                <span>{institutionCode}</span>
              </>
            )}
          </div>
          <button
            onClick={onClear}
            className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear chat
          </button>
        </div>
      )}

      {/* Composer box */}
      <div className="relative">
        {/* Slash command menu */}
        <AnimatePresence>
          {showSlash && filteredCommands.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              className="absolute bottom-full mb-1.5 left-0 right-0 rounded-xl border border-border bg-popover shadow-lg z-50 overflow-hidden"
            >
              {filteredCommands.map((cmd) => (
                <button
                  key={cmd.cmd}
                  onClick={() => applySlash(cmd)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-muted transition-colors"
                >
                  <Hash className="h-3.5 w-3.5 text-indigo-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-foreground">{cmd.label}</p>
                    <p className="text-[10px] text-muted-foreground">{cmd.desc}</p>
                  </div>
                  <span className="ml-auto text-[10px] font-mono text-muted-foreground">{cmd.cmd}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-end gap-2 rounded-2xl border border-border bg-muted/40 px-4 py-3 focus-within:border-indigo-400 focus-within:bg-background transition-all shadow-sm">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder={placeholder}
            disabled={isLoading || disabled}
            aria-label="Message input"
            className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
            style={{ minHeight: "24px", maxHeight: "160px" }}
          />
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {/* Multi-agent toggle */}
            <button
              onClick={onToggleMultiAgent}
              title={useMultiAgentMode ? "Multi-agent mode on" : "Multi-agent mode off"}
              aria-label="Toggle multi-agent mode"
              className={cn(
                "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors",
                useMultiAgentMode
                  ? "bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <Zap className="h-3 w-3" />
              {useMultiAgentMode ? "Multi" : "Auto"}
            </button>
            {/* Send button */}
            <button
              onClick={() => onSubmit(value)}
              disabled={isLoading || !value.trim() || disabled}
              aria-label="Send message"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
        {useMultiAgentMode
          ? "Multi-agent — complex queries engage multiple specialists"
          : "Auto-routing — AQAA selects the right agent · Shift+Enter for newline · / for commands"}
      </p>
    </div>
  );
}

// ── Main workspace view ───────────────────────────────────────────────────────

export function AiWorkspaceView() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "system_admin";
  const queryClient = useQueryClient();

  const [institutionCode, setInstitutionCode] = useState<string>(
    isAdmin ? "" : (user as Record<string, string> | null)?.institution_code ?? "TUT"
  );
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<WorkspaceMessage[]>([]);
  const [input, setInput] = useState("");
  const [useMultiAgentMode, setUseMultiAgentMode] = useState(false);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [isStreamLoading, setIsStreamLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: suggestedData } = useSuggestedPrompts(institutionCode || undefined);
  const ask = useAsk();
  const agentRouter = useAgentRouter();
  const multiAgent = useMultiAgent();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();

  const isLoading = ask.isPending || agentRouter.isPending || multiAgent.isPending || isStreamLoading;
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant") ?? null;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Handle ?q= pre-filled query from MiniAIWidget / AISuggestions
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q) {
      setInput(q);
      // Clear from URL without reload
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const exportAnswer = useCallback((content: string) => {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aqaa-answer-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleNewSession = useCallback(async () => {
    try {
      const session = await createSession.mutateAsync({
        mode: "qa_assistant",
        institution_code: institutionCode || undefined,
      });
      setActiveSessionId(session.id);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    } catch {
      setMessages([]);
      setActiveSessionId(null);
    }
  }, [createSession, institutionCode, queryClient]);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      await deleteSession.mutateAsync(id);
      if (id === activeSessionId) { setActiveSessionId(null); setMessages([]); }
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    [deleteSession, activeSessionId, queryClient]
  );

  const handleSubmit = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || isLoading) return;
      if (isAdmin && !institutionCode) {
        toast.error("Select an institution first");
        return;
      }

      const userMsg: WorkspaceMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: q,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      if (showRightPanel === false) setShowRightPanel(true);

      if (useMultiAgentMode) {
        try {
          const result: MultiAgentResponse = await multiAgent.mutateAsync({
            prompt: q,
            institution_code: institutionCode || null,
            context_limit: 5,
            session_id: activeSessionId,
          });
          const contributions = result.contributions?.map((c) => ({
            agent: c.agent,
            confidence: c.confidence,
            summary: c.answer?.slice(0, 80),
          })) ?? [];
          const assistantMsg: WorkspaceMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: result.final_answer,
            agents: result.agents_used,
            isMultiAgent: result.is_multi_agent,
            confidence: result.overall_confidence,
            sources: result.contributions.flatMap((c) => c.sources),
            nextActions: result.suggested_next_actions,
            followUps: result.follow_up_questions,
            provider: result.provider,
            model: result.model,
            timestamp: new Date(),
            contributions,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        } catch {
          setMessages((prev) => [...prev, {
            id: crypto.randomUUID(), role: "assistant",
            content: "An error occurred. Please try again.",
            timestamp: new Date(),
          }]);
        }
        return;
      }

      // Single-agent path — streaming
      const streamMsgId = crypto.randomUUID();
      const pendingMsg: WorkspaceMessage = {
        id: streamMsgId,
        role: "assistant",
        content: "",
        agents: [],
        isMultiAgent: false,
        isStreaming: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, pendingMsg]);
      setIsStreamLoading(true);

      try {
        const abortCtrl = new AbortController();
        for await (const event of askStream(
          {
            question: q,
            institution_code: institutionCode || null,
            context_limit: 5,
            mode: "qa_assistant",
          },
          abortCtrl.signal,
        )) {
          if (event.type === "start") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamMsgId
                  ? { ...m, agents: event.agents }
                  : m,
              ),
            );
          } else if (event.type === "chunk") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamMsgId
                  ? { ...m, content: m.content + event.content }
                  : m,
              ),
            );
          } else if (event.type === "sources") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamMsgId
                  ? {
                      ...m,
                      sources: event.sources,
                      confidence: event.confidence_score,
                      nextActions: event.suggested_next_actions,
                      followUps: event.follow_up_questions,
                    }
                  : m,
              ),
            );
          } else if (event.type === "done") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamMsgId
                  ? {
                      ...m,
                      isStreaming: false,
                      provider: event.provider,
                      model: event.model,
                    }
                  : m,
              ),
            );
          } else if (event.type === "error") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === streamMsgId
                  ? {
                      ...m,
                      isStreaming: false,
                      content: m.content || "An error occurred. Please try again.",
                    }
                  : m,
              ),
            );
          }
        }
      } catch {
        // Non-stream fallback
        try {
          const result = await ask.mutateAsync({
            question: q,
            institution_code: institutionCode || null,
            context_limit: 5,
            mode: "qa_assistant",
            session_id: activeSessionId,
          });
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamMsgId
                ? {
                    ...m,
                    isStreaming: false,
                    content: result.answer,
                    confidence: result.confidence_score,
                    sources: result.sources,
                    provider: result.provider,
                    model: result.model,
                  }
                : m,
            ),
          );
        } catch {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamMsgId
                ? {
                    ...m,
                    isStreaming: false,
                    content: "An error occurred. Please try again.",
                  }
                : m,
            ),
          );
        }
      } finally {
        setIsStreamLoading(false);
        if (activeSessionId) {
          queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
        }
      }
    },
    [ask, multiAgent, institutionCode, isAdmin, activeSessionId, isLoading, useMultiAgentMode, queryClient, showRightPanel]
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] overflow-hidden bg-background">
      {/* Left sidebar */}
      <LeftSidebar
        activeSessionId={activeSessionId}
        onSelect={(id) => { setActiveSessionId(id); setMessages([]); }}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
        institutionCode={institutionCode}
        isAdmin={isAdmin}
        onInstitutionChange={setInstitutionCode}
      />

      {/* Center panel */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden bg-background">
        {/* Top bar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-background flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 shadow-sm shadow-indigo-500/20">
              <Brain className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-foreground leading-none">AQAA AI Workspace</h1>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {useMultiAgentMode ? "Multi-agent mode" : "Auto-routing mode"} · {institutionCode || "Platform"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Alert when admin has no institution */}
            {isAdmin && !institutionCode && (
              <div className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950/40 dark:border-amber-800 px-2.5 py-1.5 text-xs text-amber-700 dark:text-amber-300">
                <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
                Select an institution
              </div>
            )}

            {/* Toggle right panel */}
            <button
              onClick={() => setShowRightPanel((v) => !v)}
              aria-label={showRightPanel ? "Hide sources panel" : "Show sources panel"}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              {showRightPanel ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
              <span className="hidden sm:inline">Sources</span>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-6 py-6 space-y-5">
          {messages.length === 0 && !isLoading ? (
            <EmptyState onSubmit={handleSubmit} suggestedData={suggestedData} />
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble
                  key={msg.id}
                  msg={msg}
                  onFollowUp={handleSubmit}
                  onExport={exportAnswer}
                  isLatest={i === messages.length - 1}
                />
              ))}
              {multiAgent.isPending && (
                <ThinkingAnimation isMultiAgent={true} />
              )}
              <div ref={bottomRef} />
            </>
          )}
        </div>

        {/* Composer */}
        <PromptComposer
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          disabled={isAdmin && !institutionCode}
          useMultiAgentMode={useMultiAgentMode}
          onToggleMultiAgent={() => setUseMultiAgentMode((v) => !v)}
          institutionCode={institutionCode}
          isAdmin={isAdmin}
          messageCount={messages.length}
          onClear={() => { setMessages([]); setActiveSessionId(null); }}
        />
      </div>

      {/* Right panel */}
      <AnimatePresence>
        {showRightPanel && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 288, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <RightPanel
              message={lastAssistantMsg}
              onClose={() => setShowRightPanel(false)}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
