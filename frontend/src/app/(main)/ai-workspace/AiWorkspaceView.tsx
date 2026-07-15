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
import {
  askStream,
  type StreamSource, type Citation, type RegulatoryCitationItem,
  type StreamContextEvent, type StructuredBlock,
} from "@/lib/api/ai-assistant";
import { MarkdownMessage } from "@/components/ai/MarkdownMessage";
import { ContextPanel } from "@/components/ai/ContextPanel";
import { ArtifactPanel } from "@/components/ai/ArtifactPanel";
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

interface RegulatoryData {
  citations: RegulatoryCitationItem[];
  effective_frameworks: string[];
  requires_human_review: boolean;
  generation_mode: "LLM" | "DETERMINISTIC_TEMPLATE" | "HYBRID" | "MANUAL_REVIEW_REQUIRED";
  caveat: string | null;
}

interface WorkspaceMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  isMultiAgent?: boolean;
  isStreaming?: boolean;
  confidence?: number;
  structuredBlocks?: StructuredBlock[];
  executionSummary?: string;
  sources?: StreamSource[];
  nextActions?: string[];
  followUps?: string[];
  provider?: string;
  model?: string;
  timestamp: Date;
  citations?: Citation[];
  unsupportedClaims?: string[];
  regulatoryData?: RegulatoryData;
  groundingStatus?: "grounded" | "partially_grounded" | "no_source_found";
  groundingScore?: number;
  isError?: boolean;
  errorMessage?: string;
}

// ── Context indicator bar (D4) ─────────────────────────────────────────────────

function ContextIndicatorBar({ ctx }: { ctx: StreamContextEvent | null }) {
  if (!ctx || !ctx.institution_code) return null;

  const parts = Object.entries(ctx.indicator ?? {}).filter(([, v]) => v);
  if (parts.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 px-5 py-2 border-b border-border bg-muted/30 text-[11px] text-muted-foreground overflow-x-auto scrollbar-hide flex-shrink-0">
      <Building2 className="h-3 w-3 flex-shrink-0 text-blue-500" />
      {parts.map(([key, val], i) => (
        <span key={key} className="flex items-center gap-1.5 flex-shrink-0">
          {i > 0 && <ChevronRight className="h-2.5 w-2.5 text-muted-foreground/40" />}
          <span className={cn(
            "font-medium",
            key === "institution" ? "text-foreground" : "text-muted-foreground",
          )}>
            {val}
          </span>
        </span>
      ))}
      {ctx.open_finding_count > 0 && (
        <span className="ml-auto flex-shrink-0 flex items-center gap-1 bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 rounded-full px-2 py-0.5">
          <AlertCircle className="h-2.5 w-2.5" />
          {ctx.open_finding_count} open findings
        </span>
      )}
    </div>
  );
}

// ── Structured blocks panel (D5) ───────────────────────────────────────────────

function StructuredBlocksPanel({
  blocks, executionSummary,
}: {
  blocks: StructuredBlock[];
  executionSummary?: string;
}) {
  if (!blocks || blocks.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      {executionSummary && (
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground bg-muted/40 rounded-lg px-3 py-1.5">
          <Zap className="h-3 w-3 text-blue-500 flex-shrink-0" />
          {executionSummary}
        </div>
      )}
      {blocks.map((block, i) => {
        if (block.type === "findings_summary" && block.findings) {
          return (
            <div key={i} className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-950/20 px-3.5 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-amber-700 dark:text-amber-400 mb-2">
                Open Findings ({block.count ?? block.findings.length})
              </p>
              <div className="space-y-1.5">
                {block.findings.slice(0, 5).map((f) => (
                  <div key={f.id} className="flex items-start gap-2 text-[12px]">
                    <span className={cn(
                      "flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                      f.severity === "critical" ? "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-400" :
                      f.severity === "major" ? "bg-orange-100 text-orange-700 dark:bg-orange-950/50 dark:text-orange-400" :
                      "bg-yellow-100 text-yellow-700 dark:bg-yellow-950/50 dark:text-yellow-400",
                    )}>
                      {f.severity}
                    </span>
                    <div className="min-w-0">
                      <p className="font-medium text-foreground text-[12px] leading-tight">
                        {f.title || f.finding_type.replace(/_/g, " ")}
                      </p>
                      <p className="text-[11px] text-muted-foreground truncate">{f.description}</p>
                      <span className="text-[10px] text-muted-foreground/70">{f.status.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }
        if (block.type === "applicable_frameworks" && block.frameworks) {
          return (
            <div key={i} className="rounded-lg border border-border bg-muted/40 px-3.5 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5">Applicable Frameworks</p>
              <div className="flex flex-wrap gap-1.5">
                {block.frameworks.map((fw) => (
                  <span key={fw} className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-0.5 text-[11px] font-medium text-foreground">
                    <Shield className="h-2.5 w-2.5 text-blue-500" />
                    {fw}
                  </span>
                ))}
              </div>
            </div>
          );
        }
        if (block.type === "caveat" && block.text) {
          return (
            <div key={i} className="flex items-start gap-2.5 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/30 px-3.5 py-2.5">
              <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-800 dark:text-blue-300 leading-relaxed whitespace-pre-wrap">{block.text}</p>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}

// ── Action confirmation UI (D6) ────────────────────────────────────────────────

function ActionConfirmationCard({
  action, onConfirm, onCancel,
}: {
  action: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-4 space-y-3 my-2">
      <div className="flex items-start gap-3">
        <AlertCircle className="h-4.5 w-4.5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-amber-800 dark:text-amber-300 text-sm">Confirm Action</p>
          <p className="text-[13px] text-amber-700 dark:text-amber-400 mt-0.5">{action}</p>
        </div>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700 transition-colors"
        >
          Confirm
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
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

        {/* Regulatory panel */}
        {msg.regulatoryData && !msg.isStreaming && (
          <div className="mt-3 space-y-2">
            {/* Human review banner */}
            {msg.regulatoryData.requires_human_review && (
              <div className="flex items-start gap-2.5 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 px-3.5 py-2.5">
                <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-medium">
                  Manual Review Required — conflicting regulatory requirements detected. Consult your QA Officer before acting on this response.
                </p>
              </div>
            )}
            {/* Caveat */}
            {msg.regulatoryData.caveat && (
              <div className="flex items-start gap-2.5 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/30 px-3.5 py-2.5">
                <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-blue-800 dark:text-blue-300 leading-relaxed whitespace-pre-wrap">{msg.regulatoryData.caveat}</p>
              </div>
            )}
            {/* Effective frameworks */}
            {msg.regulatoryData.effective_frameworks.length > 0 && (
              <div className="rounded-lg border border-border bg-muted/40 px-3.5 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5">Applicable Frameworks</p>
                <div className="flex flex-wrap gap-1.5">
                  {msg.regulatoryData.effective_frameworks.map((fw) => (
                    <span key={fw} className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-0.5 text-[11px] font-medium text-foreground">
                      <Shield className="h-2.5 w-2.5 text-blue-500" />
                      {fw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Regulatory citations */}
            {msg.regulatoryData.citations.length > 0 && (
              <div className="rounded-lg border border-border bg-muted/40 px-3.5 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">Regulatory Citations</p>
                <div className="space-y-1.5">
                  {msg.regulatoryData.citations.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 text-[12px]">
                      <Hash className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <span className="font-medium text-foreground">{c.framework_code}</span>
                        <span className="text-muted-foreground"> v{c.version_number}</span>
                        {c.standard_code && <span className="text-muted-foreground"> · {c.standard_code}</span>}
                        <span className="text-muted-foreground truncate block text-[11px]">{c.framework_name}</span>
                        {c.is_test_fixture && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded font-medium dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800">
                            TEST FIXTURE
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Generation mode badge */}
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-muted-foreground">Generated via</span>
              <span className="text-[10px] font-medium text-foreground bg-muted px-2 py-0.5 rounded-full">
                {msg.regulatoryData.generation_mode.replace(/_/g, " ")}
              </span>
            </div>
          </div>
        )}

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

        {/* D5 Structured blocks panel */}
        {!msg.isStreaming && msg.structuredBlocks && msg.structuredBlocks.length > 0 && (
          <StructuredBlocksPanel
            blocks={msg.structuredBlocks}
            executionSummary={msg.executionSummary}
          />
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

// ── File attachment types ──────────────────────────────────────────────────────

type AttachmentStatus = "uploading" | "ready" | "error";

interface AttachedFile {
  localId: string;        // temp key
  name: string;
  sizeBytes: number;
  status: AttachmentStatus;
  file_id?: string;       // populated after successful upload (File.id from backend)
  upload_state?: string;  // backend upload_state (ready | quarantined | failed)
  errorMsg?: string;
}

const MAX_FILE_MB = 50;
const ALLOWED_TYPES = new Set([
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/zip",
  "text/plain",
  "text/csv",
  "image/png",
  "image/jpeg",
]);

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Prompt composer ────────────────────────────────────────────────────────────

function PromptComposer({
  value, onChange, onSubmit, isLoading, disabled, institutionCode, isAdmin,
  messageCount, onClear, abortRef, moduleId,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (q: string, attachedFileIds?: string[]) => void;
  isLoading: boolean;
  disabled: boolean;
  institutionCode: string;
  isAdmin: boolean;
  messageCount: number;
  onClear: () => void;
  abortRef: React.RefObject<AbortController | null>;
  moduleId?: string;
}) {
  const [showSlash, setShowSlash] = useState(false);
  const [slashFilter, setSlashFilter] = useState("");
  const [slashSelected, setSlashSelected] = useState(0);
  const [attachments, setAttachments] = useState<AttachedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredCommands = SLASH_COMMANDS.filter(
    (c) => c.cmd.slice(1).startsWith(slashFilter) || c.label.toLowerCase().startsWith(slashFilter),
  );

  const uploadFile = useCallback(async (file: File) => {
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      toast.error(`${file.name} exceeds ${MAX_FILE_MB} MB limit`);
      return;
    }
    if (!ALLOWED_TYPES.has(file.type) && file.type !== "") {
      toast.error(`${file.name}: unsupported file type`);
      return;
    }
    if (!moduleId) {
      toast.error("Select a module in the workspace context before attaching files.");
      return;
    }

    const localId = crypto.randomUUID();
    setAttachments((prev) => [...prev, {
      localId,
      name: file.name,
      sizeBytes: file.size,
      status: "uploading",
    }]);

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("module_id", moduleId);
      form.append("category", "other");
      const res = await fetch("/api/proxy/ai-assistant/attach", {
        method: "POST",
        credentials: "include",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      const data = await res.json() as { file_id: string; upload_state: string };
      if (data.upload_state === "quarantined") {
        throw new Error("File was quarantined during security scan. Contact your system administrator.");
      }
      setAttachments((prev) => prev.map((a) =>
        a.localId === localId
          ? { ...a, status: "ready", file_id: data.file_id, upload_state: data.upload_state }
          : a,
      ));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setAttachments((prev) => prev.map((a) =>
        a.localId === localId ? { ...a, status: "error", errorMsg: msg } : a,
      ));
      toast.error(`Failed to attach ${file.name}: ${msg}`);
    }
  }, [moduleId]);

  const handleFilesSelected = useCallback((files: FileList | File[]) => {
    Array.from(files).forEach(uploadFile);
  }, [uploadFile]);

  const retryAttachment = useCallback((localId: string, file?: File) => {
    if (!file) {
      setAttachments((prev) => prev.filter((a) => a.localId !== localId));
      return;
    }
    setAttachments((prev) => prev.filter((a) => a.localId !== localId));
    uploadFile(file);
  }, [uploadFile]);

  const removeAttachment = useCallback((localId: string) => {
    setAttachments((prev) => prev.filter((a) => a.localId !== localId));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleFilesSelected(e.dataTransfer.files);
    }
  }, [handleFilesSelected]);

  const doSubmit = useCallback(() => {
    const readyIds = attachments
      .filter((a) => a.status === "ready" && a.file_id)
      .map((a) => a.file_id as string);
    const uploading = attachments.some((a) => a.status === "uploading");
    if (uploading) {
      toast.warning("Please wait for all files to finish uploading");
      return;
    }
    onSubmit(value, readyIds.length > 0 ? readyIds : undefined);
    setAttachments([]);
  }, [attachments, value, onSubmit]);

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
      doSubmit();
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
    <div
      className="border-t border-border bg-background/95 backdrop-blur-sm px-4 py-3"
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={Array.from(ALLOWED_TYPES).join(",")}
        className="hidden"
        onChange={(e) => { if (e.target.files) { handleFilesSelected(e.target.files); e.target.value = ""; } }}
      />

      {/* Drag-over overlay */}
      {isDragOver && (
        <div className="mb-2 rounded-xl border-2 border-dashed border-blue-400 bg-blue-50/50 dark:bg-blue-950/20 py-4 text-center text-sm text-blue-600 dark:text-blue-400">
          Drop files here to attach
        </div>
      )}

      {/* Attached files tray */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {attachments.map((att) => (
            <div
              key={att.localId}
              className={cn(
                "flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[11px] max-w-[200px]",
                att.status === "ready" && "border-green-300 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950/30 dark:text-green-400",
                att.status === "uploading" && "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-400",
                att.status === "error" && "border-red-300 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400",
              )}
            >
              {att.status === "uploading" && <Loader2 className="h-3 w-3 flex-shrink-0 animate-spin" />}
              {att.status === "ready" && <CheckCircle2 className="h-3 w-3 flex-shrink-0" />}
              {att.status === "error" && <AlertCircle className="h-3 w-3 flex-shrink-0" />}
              <span className="truncate flex-1 min-w-0" title={att.name}>{att.name}</span>
              <span className="text-[10px] opacity-70 flex-shrink-0">{formatBytes(att.sizeBytes)}</span>
              <button
                type="button"
                onClick={() => removeAttachment(att.localId)}
                className="flex-shrink-0 ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
                aria-label={`Remove ${att.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

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
        {/* Attach button */}
        <button
          type="button"
          className="ml-3 mb-3 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0 relative"
          aria-label="Attach file"
          onClick={() => {
            if (!moduleId) {
              toast.error("Select a module in the workspace context before attaching files.");
              return;
            }
            fileInputRef.current?.click();
          }}
        >
          <Paperclip className="h-4 w-4" />
          {attachments.length > 0 && (
            <span className="absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full bg-blue-600 text-[8px] text-white flex items-center justify-center font-bold">
              {attachments.length}
            </span>
          )}
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
            onClick={doSubmit}
            disabled={(!value.trim() && !attachments.some(a => a.status === "ready" && a.file_id)) || disabled}
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
  const [rightTab, setRightTab] = useState<"context" | "artifacts">("context");
  const [isStreamLoading, setIsStreamLoading] = useState(false);
  const [lastPrompt, setLastPrompt] = useState<string>("");
  // D1 — Resolved context from the last ask-stream request
  const [resolvedContext, setResolvedContext] = useState<StreamContextEvent | null>(null);
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null);
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

  const handleSubmit = useCallback(async (question: string, attachedFileIds?: string[]) => {
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
        {
          question: q,
          institution_code: institutionCode || null,
          context_limit: 5,
          mode: "qa_assistant",
          attached_file_ids: attachedFileIds,
        },
        abortRef.current.signal,
      )) {
        if (event.type === "context") {
          // D1 — update the context indicator bar
          setResolvedContext(event);
          if (event.module_id) setActiveModuleId(event.module_id);
        } else if (event.type === "plan") {
          // D2 — execution plan (internal; no visible update needed)
        } else if (event.type === "structured") {
          // D5 — structured blocks (findings, frameworks, caveats)
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m,
              structuredBlocks: event.blocks,
              executionSummary: event.execution_summary,
            } : m,
          ));
        } else if (event.type === "start") {
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
        } else if (event.type === "regulatory") {
          setMessages((prev) => prev.map((m) =>
            m.id === streamMsgId ? {
              ...m,
              regulatoryData: {
                citations: event.citations,
                effective_frameworks: event.effective_frameworks,
                requires_human_review: event.requires_human_review,
                generation_mode: event.generation_mode,
                caveat: event.caveat,
              },
              nextActions: event.suggested_next_actions,
              followUps: event.follow_up_questions,
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

        {/* D4 — Context indicator bar */}
        <ContextIndicatorBar ctx={resolvedContext} />

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
          moduleId={activeModuleId ?? undefined}
        />
      </div>

      {/* ── Right panel — Context or Artifacts ───────────────────────────── */}
      <AnimatePresence>
        {showRightPanel && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 300, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden flex-shrink-0 border-l border-border flex flex-col"
          >
            {/* Tab bar */}
            <div className="flex border-b border-border flex-shrink-0">
              <button
                type="button"
                onClick={() => setRightTab("context")}
                className={cn(
                  "flex-1 py-2.5 text-xs font-semibold transition-colors",
                  rightTab === "context"
                    ? "border-b-2 border-blue-500 text-blue-600 dark:text-blue-400"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                Context
              </button>
              <button
                type="button"
                onClick={() => setRightTab("artifacts")}
                className={cn(
                  "flex-1 py-2.5 text-xs font-semibold transition-colors",
                  rightTab === "artifacts"
                    ? "border-b-2 border-blue-500 text-blue-600 dark:text-blue-400"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                Artifacts
              </button>
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-hidden">
              {rightTab === "context" ? (
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
              ) : (
                <ArtifactPanel
                  conversationId={activeSessionId}
                  onClose={() => setShowRightPanel(false)}
                />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
