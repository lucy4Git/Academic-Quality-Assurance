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
  useAsk, useSuggestedPrompts, useCreateSession, useChatSessions, useDeleteSession,
} from "@/hooks/useAiAssistant";
import { useMultiAgent, type MultiAgentResponse } from "@/hooks/useWorkspace";
import { askStream, type StreamSource, type Citation } from "@/lib/api/ai-assistant";
import { MarkdownMessage } from "@/components/ai/MarkdownMessage";
import { ContextPanel } from "@/components/ai/ContextPanel";
import {
  Brain, Plus, Trash2, Download, BookOpen, Zap, Shield,
  BarChart2, Search, GitBranch, GraduationCap, CheckSquare, Layers,
  Copy, Send, MessageSquare, Clock, Building2, X, PanelRightClose,
  PanelRightOpen, CheckCircle2, Loader2, ArrowRight, FileText,
  RotateCcw, Star, AlertCircle, Sparkles, Hash, Settings,
  Menu, Pin, PinOff, Mic, Paperclip, StopCircle, ChevronDown,
  ChevronRight, Search as SearchIcon, RefreshCw, Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Constants ─────────────────────────────────────────────────────────────────

const ACTIVE_INSTITUTIONS = ["TUT", "UP"];

const SLASH_COMMANDS = [
  { cmd: "/new",         label: "New Conversation",   desc: "Start fresh",                    mode: "qa_assistant" },
  { cmd: "/audit",       label: "Audit Query",         desc: "Analyse audit evidence",          mode: "audit_summary" },
  { cmd: "/policy",      label: "Policy Search",       desc: "Search institution policy",       mode: "qa_assistant" },
  { cmd: "/module",      label: "Module Query",        desc: "Query module information",         mode: "qa_assistant" },
  { cmd: "/programme",   label: "Programme Review",    desc: "Review programme quality",         mode: "qa_assistant" },
  { cmd: "/evidence",    label: "Evidence Check",      desc: "Check module evidence",            mode: "evidence" },
  { cmd: "/finding",     label: "Finding Query",       desc: "Search audit findings",            mode: "qa_assistant" },
  { cmd: "/help",        label: "Help",                desc: "Show available commands",          mode: "qa_assistant" },
  { cmd: "/report",      label: "Generate Report",     desc: "Create a QA report",              mode: "reporting" },
  { cmd: "/qualification", label: "Qualification",     desc: "NQF/credit analysis",             mode: "qualification" },
];

const THINKING_STEPS = [
  "Understanding request",
  "Searching institutional knowledge",
  "Routing to specialist agent",
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

// ── Types ─────────────────────────────────────────────────────────────────────

interface WorkspaceMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  isMultiAgent?: boolean;
  isStreaming?: boolean;
  confidence?: number;
  sources?: StreamSource[];
  nextActions?: string[];
  followUps?: string[];
  provider?: string;
  model?: string;
  timestamp: Date;
  citations?: Citation[];
  unsupportedClaims?: string[];
  groundingStatus?: "grounded" | "partially_grounded" | "no_source_found";
  groundingScore?: number;
  isError?: boolean;
  errorMessage?: string;
}

// ── AI error card ─────────────────────────────────────────────────────────────

function AiErrorCard({
  message, onRetry, isSystemAdmin,
}: {
  message: string; onRetry?: () => void; isSystemAdmin?: boolean;
}) {
  const friendlyMessage = message.includes("401") || message.includes("403")
    ? "Authentication required. Please sign in again."
    : /\b5\d\d\b/.test(message)
    ? "The AI service is temporarily unavailable. The system is using a local template provider. Configure AI_PROVIDER in backend/.env for a production LLM."
    : message.includes("No institution") || message.includes("institution_code")
    ? "No institution context was found. Please ensure your account has an institution assigned."
    : message.includes("No sources") || message.includes("no_source_found")
    ? "No institutional knowledge sources were found for your query. Try refining your question or uploading more evidence."
    : "The AI assistant could not complete the request. Please try again.";

  return (
    <div className="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-4 space-y-3 my-2">
      <div className="flex items-start gap-3">
        <AlertCircle className="h-4.5 w-4.5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-amber-800 dark:text-amber-300 text-sm">Assistant Notice</p>
          <p className="text-[13px] text-amber-700 dark:text-amber-400 mt-0.5 leading-relaxed">{friendlyMessage}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 dark:border-amber-700 px-3 py-1.5 text-xs font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors"
          >
            <RotateCcw className="h-3 w-3" /> Retry
          </button>
        )}
        {isSystemAdmin && (
          <a
            href="/settings/ai-providers"
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 dark:border-amber-700 px-3 py-1.5 text-xs font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors"
          >
            <Settings className="h-3 w-3" /> Configure AI
          </a>
        )}
      </div>
    </div>
  );
}

// ── Thinking animation ────────────────────────────────────────────────────────

function ThinkingAnimation() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    setStep(0);
    const t = setInterval(() => setStep((s) => Math.min(s + 1, THINKING_STEPS.length - 1)), 1600);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-tl-sm border border-border bg-card px-5 py-4 shadow-sm max-w-sm">
        <div className="flex items-center gap-2 mb-3">
          <div className="h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
            <Brain className="h-3 w-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-blue-600">AQAA is analysing…</span>
        </div>
        <div className="space-y-2">
          {THINKING_STEPS.map((s, i) => (
            <motion.div
              key={s}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: i <= step ? 1 : 0.2, x: 0 }}
              transition={{ duration: 0.3 }}
              className={cn("flex items-center gap-2 text-xs",
                i < step ? "text-muted-foreground"
                : i === step ? "text-blue-600 font-medium"
                : "text-muted-foreground/30"
              )}
            >
              {i < step ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
              ) : i === step ? (
                <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin flex-shrink-0" />
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

// ── Message bubble ─────────────────────────────────────────────────────────────

const MessageBubble = memo(function MessageBubble({
  msg, onFollowUp, onRetry, isSystemAdmin,
}: {
  msg: WorkspaceMessage;
  onFollowUp: (q: string) => void;
  onRetry?: () => void;
  isSystemAdmin?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copied to clipboard");
  };

  const exportMarkdown = () => {
    const md = [
      `# AQAA Response — ${msg.timestamp.toLocaleDateString()}`,
      "",
      msg.content,
      "",
      msg.citations?.length
        ? ["## Sources", ...msg.citations.map((c, i) => `${i + 1}. **${c.title}** (${c.entity_type})\n   > ${c.snippet ?? ""}`)].join("\n")
        : "",
    ].join("\n");
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aqaa-response-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // User bubble
  if (msg.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22 }}
        className="flex justify-end"
      >
        <div className="max-w-[72%] group">
          <div className="rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-3 text-sm text-white shadow-sm">
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

  // Error bubble
  if (msg.isError) {
    return (
      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
        <AiErrorCard message={msg.errorMessage ?? ""} onRetry={onRetry} isSystemAdmin={isSystemAdmin} />
      </motion.div>
    );
  }

  // Assistant bubble
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      className="flex justify-start"
    >
      <div className="max-w-[88%] w-full group">
        {/* Avatar + agent badge */}
        <div className="flex items-center gap-2 mb-2">
          <div className="h-6 w-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
            <Brain className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-xs font-semibold text-foreground">AQAA</span>
          {msg.agents && msg.agents.length > 0 && (
            <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
              {msg.agents[0]?.replace(/_/g, " ")}
            </span>
          )}
          {msg.groundingStatus === "grounded" && (
            <span className="text-[10px] text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded-full">
              Grounded
            </span>
          )}
          <span className="text-[10px] text-muted-foreground ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
            {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {/* Content */}
        <div className="rounded-2xl rounded-tl-sm border border-border bg-card px-5 py-4 shadow-sm">
          <MarkdownMessage
            content={msg.content}
            citations={msg.citations ?? []}
            isStreaming={msg.isStreaming}
          />
        </div>

        {/* Action toolbar */}
        {!msg.isStreaming && msg.content && (
          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label="Copy response"
            >
              {copied ? <CheckCircle2 className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              type="button"
              onClick={exportMarkdown}
              className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label="Export as Markdown"
            >
              <Download className="h-3 w-3" />
              Export .md
            </button>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label="Regenerate"
              >
                <RotateCcw className="h-3 w-3" />
                Regenerate
              </button>
            )}
          </div>
        )}

        {/* Follow-up suggestions */}
        {!msg.isStreaming && msg.followUps && msg.followUps.length > 0 && (
          <div className="mt-3 space-y-1.5">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground px-1">
              Suggested follow-ups
            </p>
            <div className="flex flex-wrap gap-2">
              {msg.followUps.slice(0, 3).map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => onFollowUp(q)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-[12px] text-foreground hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/30 transition-all"
                >
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
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

// ── Conversation sidebar ───────────────────────────────────────────────────────

function ConversationSidebar({
  activeSessionId, onSelect, onNew, onDelete, onPin,
  institutionCode, isAdmin, onInstitutionChange, pinnedIds,
}: {
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onPin: (id: string) => void;
  institutionCode: string;
  isAdmin: boolean;
  onInstitutionChange: (code: string) => void;
  pinnedIds: Set<string>;
}) {
  const { data: sessions } = useChatSessions();
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = sessions?.filter((s) =>
    !searchQuery || (s.title ?? s.mode).toLowerCase().includes(searchQuery.toLowerCase())
  ) ?? [];

  const pinned = filtered.filter((s) => pinnedIds.has(s.id));
  const recent = filtered.filter((s) => !pinnedIds.has(s.id));

  function SessionRow({ s }: { s: typeof filtered[number] }) {
    return (
      <div
        role="button"
        tabIndex={0}
        aria-label={`Open: ${s.title ?? s.mode}`}
        onKeyDown={(e) => e.key === "Enter" && onSelect(s.id)}
        onClick={() => onSelect(s.id)}
        className={cn(
          "group flex items-center justify-between gap-1 rounded-xl px-3 py-2.5 cursor-pointer transition-colors",
          s.id === activeSessionId
            ? "bg-blue-100 dark:bg-blue-950/60 text-blue-900 dark:text-blue-100"
            : "hover:bg-muted text-sidebar-foreground",
        )}
      >
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium truncate">{s.title || s.mode.replace(/_/g, " ")}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <Clock className="h-2.5 w-2.5 text-muted-foreground opacity-50" />
            <span className="text-[10px] text-muted-foreground">{s.message_count} msgs</span>
          </div>
        </div>
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onPin(s.id); }}
            className="p-1 rounded hover:bg-accent"
            aria-label={pinnedIds.has(s.id) ? "Unpin" : "Pin"}
          >
            {pinnedIds.has(s.id)
              ? <PinOff className="h-3 w-3 text-blue-500" />
              : <Pin className="h-3 w-3 text-muted-foreground" />
            }
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
            className="p-1 rounded hover:bg-destructive/10"
            aria-label="Delete"
          >
            <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-[240px] shrink-0 flex flex-col border-r border-border bg-sidebar overflow-hidden">
      {/* New chat */}
      <div className="p-3 border-b border-border">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-sm shadow-blue-500/20"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </button>
      </div>

      {/* Search */}
      <div className="px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-2.5 py-1.5">
          <SearchIcon className="h-3 w-3 text-muted-foreground flex-shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations…"
            className="flex-1 text-xs bg-transparent outline-none text-foreground placeholder:text-muted-foreground"
          />
          {searchQuery && (
            <button type="button" onClick={() => setSearchQuery("")}>
              <X className="h-3 w-3 text-muted-foreground" />
            </button>
          )}
        </div>
      </div>

      {/* Institution selector (admin) */}
      {isAdmin && (
        <div className="px-3 py-2 border-b border-border">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 px-1">
            Institution
          </p>
          <select
            value={institutionCode}
            onChange={(e) => onInstitutionChange(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">All institutions…</option>
            {ACTIVE_INSTITUTIONS.map((code) => (
              <option key={code} value={code}>{code}</option>
            ))}
          </select>
        </div>
      )}

      {/* Session list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {pinned.length > 0 && (
          <>
            <p className="px-2 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-1">
              <Pin className="h-2.5 w-2.5" /> Pinned
            </p>
            {pinned.map((s) => <SessionRow key={s.id} s={s} />)}
          </>
        )}

        <p className="px-2 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Recent
        </p>
        {recent.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <MessageSquare className="h-7 w-7 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-xs text-muted-foreground">No conversations yet</p>
            <p className="text-[10px] text-muted-foreground/50 mt-0.5">
              Start a conversation above
            </p>
          </div>
        ) : (
          recent.map((s) => <SessionRow key={s.id} s={s} />)
        )}
      </div>

      {/* Institution badge (non-admin) */}
      {!isAdmin && institutionCode && (
        <div className="px-3 py-2.5 border-t border-border">
          <div className="flex items-center gap-2 rounded-lg bg-muted/60 px-2.5 py-1.5">
            <Building2 className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
            <span className="text-xs font-medium text-foreground">{institutionCode}</span>
            <span className="text-[10px] text-muted-foreground ml-auto">Active</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Empty state ────────────────────────────────────────────────────────────────

function EmptyState({
  onSubmit, suggestedData, institutionCode,
}: {
  onSubmit: (q: string) => void;
  suggestedData?: { prompts: { prompt: string; category: string }[] } | null;
  institutionCode: string;
}) {
  const prompts = suggestedData?.prompts.length
    ? suggestedData.prompts.slice(0, 6).map((p) => ({
        category: p.category,
        label: p.prompt.slice(0, 48) + (p.prompt.length > 48 ? "…" : ""),
        prompt: p.prompt,
      }))
    : EMPTY_PROMPTS;

  return (
    <div className="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto px-4 py-8">
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="mb-6"
      >
        <div className="relative inline-flex">
          <div className="h-16 w-16 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <div className="absolute -right-1 -top-1 h-5 w-5 rounded-full bg-emerald-500 border-2 border-background flex items-center justify-center">
            <Zap className="h-2.5 w-2.5 text-white" />
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08 }}
      >
        <h2 className="text-2xl font-bold text-foreground mb-1.5 tracking-tight">
          {institutionCode ? `${institutionCode} AI Workspace` : "AQAA AI Workspace"}
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed mb-1">
          Academic Quality Intelligence at your command.
        </p>
        <p className="text-xs text-muted-foreground/60 mb-8">
          Ask anything — audits, evidence, policies, qualifications, accreditation.
          Use <kbd className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono text-[10px]">/</kbd> for commands.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.14 }}
        className="w-full"
      >
        <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
          Suggested tasks
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {prompts.map((p, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.18 + i * 0.04 }}
              whileHover={{ y: -2, transition: { duration: 0.15 } }}
              onClick={() => onSubmit(p.prompt)}
              className="rounded-xl border border-border bg-card px-4 py-3.5 text-left hover:border-blue-400 hover:shadow-md transition-all group"
            >
              <span className="block text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 group-hover:text-blue-500 transition-colors">
                {p.category}
              </span>
              <span className="text-[13px] text-foreground leading-snug">{p.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// ── Prompt composer ────────────────────────────────────────────────────────────

function PromptComposer({
  value, onChange, onSubmit, isLoading, disabled, institutionCode, isAdmin,
  messageCount, onClear, abortRef,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (q: string) => void;
  isLoading: boolean;
  disabled: boolean;
  institutionCode: string;
  isAdmin: boolean;
  messageCount: number;
  onClear: () => void;
  abortRef: React.RefObject<AbortController | null>;
}) {
  const [showSlash, setShowSlash] = useState(false);
  const [slashFilter, setSlashFilter] = useState("");
  const [slashSelected, setSlashSelected] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const filteredCommands = SLASH_COMMANDS.filter(
    (c) => c.cmd.slice(1).startsWith(slashFilter) || c.label.toLowerCase().startsWith(slashFilter),
  );

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const v = e.target.value;
    onChange(v);
    // Auto-resize
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    // Slash menu
    const lastWord = v.split(/\s/).pop() ?? "";
    if (lastWord.startsWith("/")) {
      setSlashFilter(lastWord.slice(1).toLowerCase());
      setSlashSelected(0);
      setShowSlash(true);
    } else {
      setShowSlash(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSlash) {
      if (e.key === "ArrowDown") { e.preventDefault(); setSlashSelected((s) => Math.min(s + 1, filteredCommands.length - 1)); return; }
      if (e.key === "ArrowUp") { e.preventDefault(); setSlashSelected((s) => Math.max(s - 1, 0)); return; }
      if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); applySlash(filteredCommands[slashSelected]); return; }
      if (e.key === "Escape") { setShowSlash(false); return; }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(value);
    }
  };

  const applySlash = (cmd: (typeof SLASH_COMMANDS)[number] | undefined) => {
    if (!cmd) return;
    if (cmd.cmd === "/new") { onClear(); onChange(""); setShowSlash(false); return; }
    if (cmd.cmd === "/help") {
      const helpText = SLASH_COMMANDS.map((c) => `${c.cmd} — ${c.desc}`).join("\n");
      onChange(helpText);
      setShowSlash(false);
      return;
    }
    const parts = value.split(/\s/);
    parts.pop();
    onChange(parts.join(" ") + (parts.length ? " " : "") + cmd.label + ": ");
    setShowSlash(false);
    textareaRef.current?.focus();
  };

  const placeholder = isAdmin && !institutionCode
    ? "Select an institution to begin…"
    : "Ask about audits, evidence, policies, programmes… (/ for commands, Shift+Enter for newline)";

  return (
    <div className="border-t border-border bg-background/95 backdrop-blur-sm px-4 py-3">
      {/* Session toolbar */}
      {messageCount > 0 && (
        <div className="flex items-center justify-between mb-2 text-[11px] text-muted-foreground">
          <span>{messageCount} messages</span>
          <button
            type="button"
            onClick={onClear}
            className="hover:text-foreground transition-colors"
          >
            Clear conversation
          </button>
        </div>
      )}

      {/* Slash command dropdown */}
      <AnimatePresence>
        {showSlash && filteredCommands.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15 }}
            className="mb-2 rounded-xl border border-border bg-card shadow-lg overflow-hidden"
          >
            {filteredCommands.slice(0, 8).map((cmd, i) => (
              <button
                key={cmd.cmd}
                type="button"
                onClick={() => applySlash(cmd)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors",
                  i === slashSelected ? "bg-blue-50 dark:bg-blue-950/50" : "hover:bg-muted",
                )}
              >
                <span className="font-mono text-[11px] font-bold text-blue-600 w-28 flex-shrink-0">
                  {cmd.cmd}
                </span>
                <div>
                  <span className="text-xs font-semibold text-foreground">{cmd.label}</span>
                  <span className="text-[11px] text-muted-foreground ml-2">{cmd.desc}</span>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Composer box */}
      <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-background shadow-sm focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-400/10 transition-all">
        {/* Attachment placeholder */}
        <button
          type="button"
          className="ml-3 mb-3 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
          aria-label="Attach file"
          onClick={() => toast.info("File attachments coming in Phase 4 Wave 3")}
        >
          <Paperclip className="h-4 w-4" />
        </button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none min-h-[44px] max-h-[200px] leading-relaxed"
          aria-label="AI query composer"
        />

        {/* Voice placeholder */}
        <button
          type="button"
          className="mr-1 mb-3 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
          aria-label="Voice input (coming soon)"
          onClick={() => toast.info("Voice input coming in Phase 4 Wave 3")}
        >
          <Mic className="h-4 w-4" />
        </button>

        {/* Send / Stop */}
        {isLoading ? (
          <button
            type="button"
            onClick={() => abortRef.current?.abort()}
            className="mr-3 mb-3 flex h-8 w-8 items-center justify-center rounded-xl bg-rose-100 text-rose-600 hover:bg-rose-200 dark:bg-rose-950/50 dark:text-rose-400 transition-colors flex-shrink-0"
            aria-label="Stop generation"
          >
            <StopCircle className="h-4 w-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => onSubmit(value)}
            disabled={!value.trim() || disabled}
            className="mr-3 mb-3 flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0 shadow-sm shadow-blue-500/30"
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        )}
      </div>

      <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
        AQAA auto-routes questions to the right specialist agent · / for commands
      </p>
    </div>
  );
}

// ── Main workspace view ────────────────────────────────────────────────────────

export function AiWorkspaceView() {
  const user = useAuthStore((s) => s.user);
  const router = useRouter();
  const isAdmin = user?.role === "system_admin";
  const queryClient = useQueryClient();

  const [institutionCode, setInstitutionCode] = useState<string>(
    isAdmin ? "" : (user as Record<string, string> | null)?.institution_code ?? "TUT",
  );
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<WorkspaceMessage[]>([]);
  const [input, setInput] = useState("");
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [isStreamLoading, setIsStreamLoading] = useState(false);
  const [lastPrompt, setLastPrompt] = useState<string>("");
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem("aqaa:pinned-sessions");
      return stored ? new Set(JSON.parse(stored) as string[]) : new Set();
    } catch { return new Set(); }
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const { data: suggestedData } = useSuggestedPrompts(institutionCode || undefined);
  const ask = useAsk();
  const multiAgent = useMultiAgent();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();

  const isLoading = ask.isPending || multiAgent.isPending || isStreamLoading;
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant") ?? null;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Pre-fill from URL ?q=
  useEffect(() => {
    if (typeof window === "undefined") return;
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      setInput(q);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const handlePin = useCallback((id: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      try { localStorage.setItem("aqaa:pinned-sessions", JSON.stringify(Array.from(next))); } catch {}
      return next;
    });
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

  const handleDeleteSession = useCallback(async (id: string) => {
    await deleteSession.mutateAsync(id);
    if (id === activeSessionId) { setActiveSessionId(null); setMessages([]); }
    queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
  }, [deleteSession, activeSessionId, queryClient]);

  const handleClear = useCallback(() => {
    setMessages([]);
    setActiveSessionId(null);
  }, []);

  const handleSubmit = useCallback(async (question: string) => {
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
    setLastPrompt(q);

    // Streaming path
    const streamMsgId = crypto.randomUUID();
    setMessages((prev) => [...prev, {
      id: streamMsgId, role: "assistant", content: "", isStreaming: true, timestamp: new Date(),
    }]);
    setIsStreamLoading(true);

    abortRef.current = new AbortController();

    try {
      let groundingScore: number | undefined;
      for await (const event of askStream(
        { question: q, institution_code: institutionCode || null, context_limit: 5, mode: "qa_assistant" },
        abortRef.current.signal,
      )) {
        if (event.type === "start") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? { ...m, agents: event.agents } : m,
          ));
        } else if (event.type === "chunk" || event.type === "token") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? { ...m, content: m.content + event.content } : m,
          ));
        } else if (event.type === "sources") {
          groundingScore = event.confidence_score;
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m,
              sources: event.sources,
              groundingScore: event.confidence_score,
              nextActions: event.suggested_next_actions,
              followUps: event.follow_up_questions ?? event.suggested_followups,
            } : m,
          ));
        } else if (event.type === "metadata") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m,
              citations: event.citations,
              unsupportedClaims: event.unsupported_claims,
              groundingStatus: event.grounding_status,
            } : m,
          ));
        } else if (event.type === "done") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m, isStreaming: false, provider: event.provider, model: event.model,
            } : m,
          ));
        } else if (event.type === "error") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m, isStreaming: false, isError: true, errorMessage: event.message,
            } : m,
          ));
        }
      }
    } catch (err) {
      if ((err as Error)?.name === "AbortError") {
        setMessages((prev) => prev.map((m) =>
          m.id === streamMsgId ? { ...m, isStreaming: false } : m,
        ));
      } else {
        setMessages((prev) => prev.map((m) =>
          m.id === streamMsgId ? {
            ...m, isStreaming: false, isError: true,
            errorMessage: err instanceof Error ? err.message : String(err),
          } : m,
        ));
      }
    } finally {
      setIsStreamLoading(false);
      abortRef.current = null;
    }
  }, [isLoading, isAdmin, institutionCode]);

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Left sidebar ──────────────────────────────────────────────────── */}
      <ConversationSidebar
        activeSessionId={activeSessionId}
        onSelect={(id) => { setActiveSessionId(id); setMessages([]); }}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
        onPin={handlePin}
        institutionCode={institutionCode}
        isAdmin={isAdmin}
        onInstitutionChange={setInstitutionCode}
        pinnedIds={pinnedIds}
      />

      {/* ── Main chat ─────────────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* Topbar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-background/95 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-semibold text-foreground">AI Workspace</span>
            {institutionCode && (
              <span className="text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                {institutionCode}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setShowRightPanel((v) => !v)}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label={showRightPanel ? "Hide context panel" : "Show context panel"}
            >
              {showRightPanel ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
              <span className="hidden sm:inline">{showRightPanel ? "Hide context" : "Show context"}</span>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5">
          {messages.length === 0 ? (
            <EmptyState
              onSubmit={(q) => { setInput(q); handleSubmit(q); }}
              suggestedData={suggestedData}
              institutionCode={institutionCode}
            />
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onFollowUp={(q) => { setInput(q); handleSubmit(q); }}
                onRetry={() => handleSubmit(lastPrompt)}
                isSystemAdmin={isAdmin}
              />
            ))
          )}

          {/* Thinking indicator */}
          {isLoading && !messages.some((m) => m.isStreaming) && (
            <ThinkingAnimation />
          )}

          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <PromptComposer
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          disabled={isAdmin && !institutionCode}
          institutionCode={institutionCode}
          isAdmin={isAdmin}
          messageCount={messages.length}
          onClear={handleClear}
          abortRef={abortRef}
        />
      </div>

      {/* ── Right context panel ───────────────────────────────────────────── */}
      <AnimatePresence>
        {showRightPanel && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden flex-shrink-0"
          >
            <ContextPanel
              institutionCode={institutionCode}
              groundingScore={lastAssistantMsg?.groundingScore}
              groundingStatus={lastAssistantMsg?.groundingStatus}
              sources={(lastAssistantMsg?.sources as StreamSource[]) ?? []}
              citations={lastAssistantMsg?.citations ?? []}
              agents={lastAssistantMsg?.agents ?? []}
              nextActions={lastAssistantMsg?.nextActions ?? []}
              onActionClick={(action, route) => route && router.push(route)}
              onClose={() => setShowRightPanel(false)}
              messageCount={messages.length}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
