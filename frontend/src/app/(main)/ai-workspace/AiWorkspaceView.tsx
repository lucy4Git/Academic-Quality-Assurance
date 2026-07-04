"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
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
import {
  Brain,
  Plus,
  Trash2,
  ChevronRight,
  Download,
  BookOpen,
  Zap,
  Shield,
  BarChart2,
  Search,
  GitBranch,
  GraduationCap,
  CheckSquare,
  Layers,
} from "lucide-react";

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
  qa_general: Brain,
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AgentBadge({ agent, mode }: { agent: string; mode: string }) {
  const Icon = AGENT_ICONS[agent] ?? Brain;
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
      <Icon className="h-3 w-3" />
      {agent.replace(/_/g, " ")}
    </span>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour = pct >= 70 ? "bg-green-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      <div className="h-1.5 w-24 rounded-full bg-gray-100">
        <div className={`h-1.5 rounded-full ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      <span>{pct}% confidence</span>
    </div>
  );
}

function SourceChip({ source }: { source: SourceChunk | string }) {
  if (typeof source === "string") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-gray-50 px-2 py-0.5 text-xs text-gray-600">
        <BookOpen className="h-2.5 w-2.5 text-gray-400" />
        {source}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-blue-100 bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
      <BookOpen className="h-2.5 w-2.5" />
      {source.title || source.entity_key}
      <span className="text-blue-400">({(source.relevance_score * 100).toFixed(0)}%)</span>
    </span>
  );
}

function NextActionPill({ action, onClick }: { action: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-gray-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
    >
      {action}
    </button>
  );
}

interface WorkspaceMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agents?: string[];
  isMultiAgent?: boolean;
  confidence?: number;
  sources?: (SourceChunk | string)[];
  nextActions?: string[];
  followUps?: string[];
  provider?: string;
  model?: string;
  routerResult?: AgentRouterResponse;
}

function MessageBubble({
  msg,
  onFollowUp,
  onExport,
}: {
  msg: WorkspaceMessage;
  onFollowUp: (q: string) => void;
  onExport: (content: string) => void;
}) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-3 text-sm text-white shadow-sm">
          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-3">
        {/* Agent badges */}
        {msg.agents && msg.agents.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {msg.agents.map((a) => (
              <AgentBadge key={a} agent={a} mode={a} />
            ))}
            {msg.isMultiAgent && (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 border border-purple-200 px-2.5 py-0.5 text-xs font-medium text-purple-700">
                <Zap className="h-3 w-3" />
                Multi-agent
              </span>
            )}
          </div>
        )}

        {/* Answer card */}
        <div className="rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-5 py-4 shadow-sm">
          <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{msg.content}</p>

          {/* Confidence + provider */}
          {msg.confidence !== undefined && (
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <ConfidenceBar score={msg.confidence} />
              {msg.provider && (
                <span className="text-xs text-gray-400">{msg.provider} · {msg.model}</span>
              )}
            </div>
          )}

          {/* Sources */}
          {msg.sources && msg.sources.length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1.5">Sources</p>
              <div className="flex flex-wrap gap-1.5">
                {msg.sources.slice(0, 6).map((s, i) => (
                  <SourceChip key={i} source={s} />
                ))}
              </div>
            </div>
          )}

          {/* Export */}
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => onExport(msg.content)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              <Download className="h-3 w-3" />
              Export
            </button>
          </div>
        </div>

        {/* Next actions */}
        {msg.nextActions && msg.nextActions.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 pl-1">Suggested actions</p>
            <div className="flex flex-wrap gap-1.5">
              {msg.nextActions.map((a, i) => (
                <NextActionPill key={i} action={a} onClick={() => onFollowUp(a)} />
              ))}
            </div>
          </div>
        )}

        {/* Follow-up questions */}
        {msg.followUps && msg.followUps.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 pl-1">Follow-up</p>
            <div className="flex flex-wrap gap-1.5">
              {msg.followUps.map((q, i) => (
                <button
                  key={i}
                  onClick={() => onFollowUp(q)}
                  className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Session sidebar
// ---------------------------------------------------------------------------

function WorkspaceSidebar({
  activeSessionId,
  onSelect,
  onNew,
  onDelete,
}: {
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  const { data: sessions } = useChatSessions();

  return (
    <div className="w-64 shrink-0 flex flex-col border-r border-gray-100 bg-gray-50/80">
      <div className="p-4 border-b border-gray-100">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 transition-colors shadow-sm"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {!sessions || sessions.length === 0 ? (
          <div className="px-3 py-8 text-center">
            <Brain className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-xs text-gray-400">No conversations yet</p>
            <p className="text-xs text-gray-300 mt-0.5">Start by asking AQAA a question</p>
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center justify-between gap-2 rounded-xl px-3 py-2.5 cursor-pointer transition-colors ${
                s.id === activeSessionId
                  ? "bg-indigo-100 text-indigo-900"
                  : "hover:bg-gray-100 text-gray-700"
              }`}
              onClick={() => onSelect(s.id)}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate">
                  {s.title || s.mode.replace(/_/g, " ")}
                </p>
                <p className="text-[10px] text-gray-400">{s.message_count} messages</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-all shrink-0"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      <div className="p-3 border-t border-gray-100 space-y-1">
        <p className="px-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400">Quick access</p>
        {[
          { label: "Knowledge Search", href: "/knowledge-search" },
          { label: "File Library", href: "/files" },
          { label: "Audit Centre", href: "/audits" },
          { label: "Reports", href: "/reports" },
        ].map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="flex items-center justify-between rounded-lg px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          >
            {link.label}
            <ChevronRight className="h-3 w-3 opacity-40" />
          </a>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main AI Workspace
// ---------------------------------------------------------------------------

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
  const [detectedAgent, setDetectedAgent] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { data: suggestedData } = useSuggestedPrompts(institutionCode || undefined);
  const ask = useAsk();
  const agentRouter = useAgentRouter();
  const multiAgent = useMultiAgent();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();

  const isLoading = ask.isPending || agentRouter.isPending || multiAgent.isPending;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
      if (!question.trim() || isLoading) return;
      if (isAdmin && !institutionCode) return;

      const userMsg: WorkspaceMessage = { id: crypto.randomUUID(), role: "user", content: question };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      if (useMultiAgentMode) {
        try {
          const result: MultiAgentResponse = await multiAgent.mutateAsync({
            prompt: question,
            institution_code: institutionCode || null,
            context_limit: 5,
            session_id: activeSessionId,
          });
          setDetectedAgent(result.agents_used[0] ?? null);
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
          };
          setMessages((prev) => [...prev, assistantMsg]);
        } catch {
          setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: "An error occurred. Please try again." }]);
        }
        return;
      }

      // Single-agent path: route then ask
      let routerResult: AgentRouterResponse | undefined;
      let effectiveMode = "qa_assistant";
      try {
        routerResult = await agentRouter.mutateAsync(question);
        setDetectedAgent(routerResult.intent);
        effectiveMode = routerResult.agent_mode;
      } catch { /* non-fatal */ }

      try {
        const result = await ask.mutateAsync({
          question,
          institution_code: institutionCode || null,
          context_limit: 5,
          mode: effectiveMode,
          session_id: activeSessionId,
        });
        const assistantMsg: WorkspaceMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          agents: routerResult ? [routerResult.intent] : [],
          isMultiAgent: false,
          confidence: result.confidence_score,
          sources: result.sources,
          nextActions: routerResult?.suggested_next_actions,
          followUps: routerResult?.follow_up_questions,
          provider: result.provider,
          model: result.model,
          routerResult,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        if (activeSessionId) {
          queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
        }
      } catch {
        setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: "An error occurred. Please try again." }]);
      }
    },
    [ask, agentRouter, multiAgent, institutionCode, isAdmin, activeSessionId, isLoading, useMultiAgentMode, queryClient]
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] overflow-hidden bg-gray-50/30">
      {/* Sidebar */}
      <WorkspaceSidebar
        activeSessionId={activeSessionId}
        onSelect={(id) => { setActiveSessionId(id); setMessages([]); }}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
      />

      {/* Main workspace */}
      <div className="flex flex-col flex-1 min-w-0 bg-white">
        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100 bg-white">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <Brain className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-gray-900">AQAA AI Workspace</h1>
              {detectedAgent && (
                <p className="text-xs text-indigo-600">
                  Active: {detectedAgent.replace(/_/g, " ")} agent
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Multi-agent toggle */}
            <button
              onClick={() => setUseMultiAgentMode((v) => !v)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                useMultiAgentMode
                  ? "bg-purple-100 text-purple-700 border border-purple-200"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
              title="Multi-agent mode engages multiple specialised agents for complex queries"
            >
              <Zap className="h-3 w-3" />
              Multi-agent {useMultiAgentMode ? "on" : "off"}
            </button>

            {/* Institution selector for admin */}
            {isAdmin && (
              <select
                value={institutionCode}
                onChange={(e) => setInstitutionCode(e.target.value)}
                className="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="">Select institution…</option>
                {ACTIVE_INSTITUTIONS.map((code) => (
                  <option key={code} value={code}>{code}</option>
                ))}
              </select>
            )}

            {messages.length > 0 && (
              <button
                onClick={() => { setMessages([]); setDetectedAgent(null); }}
                className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs text-gray-500 hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600 mb-4 shadow-lg shadow-indigo-200">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Ask AQAA</h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-6">
                Ask about audits, evidence, accreditation, policies, qualifications, or reports.
                AQAA automatically routes your question to the right agent.
              </p>

              {suggestedData && suggestedData.prompts.length > 0 && (
                <div className="w-full space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                    Try asking…
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {suggestedData.prompts.slice(0, 6).map((p, i) => (
                      <button
                        key={i}
                        onClick={() => handleSubmit(p.prompt)}
                        className="rounded-xl border border-gray-200 bg-white px-4 py-3 text-left text-sm text-gray-700 hover:border-indigo-300 hover:bg-indigo-50 transition-all shadow-sm"
                      >
                        <span className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
                          {p.category}
                        </span>
                        {p.prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              onFollowUp={handleSubmit}
              onExport={exportAnswer}
            />
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white px-5 py-3 shadow-sm">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-400">
                  {useMultiAgentMode ? "Consulting multiple agents…" : "Thinking…"}
                </span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-100 bg-white px-6 py-4">
          <div className="flex items-end gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 focus-within:border-indigo-300 focus-within:bg-white transition-all shadow-sm">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(input);
                }
              }}
              rows={1}
              placeholder={
                isAdmin && !institutionCode
                  ? "Select an institution to start…"
                  : "Ask about audits, evidence, policies, qualifications, or reports…"
              }
              disabled={isLoading || (isAdmin && !institutionCode)}
              className="flex-1 resize-none bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none disabled:opacity-50"
              style={{ minHeight: "24px", maxHeight: "120px" }}
            />
            <button
              onClick={() => handleSubmit(input)}
              disabled={isLoading || !input.trim() || (isAdmin && !institutionCode)}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </div>
          <p className="mt-2 text-center text-[10px] text-gray-400">
            {useMultiAgentMode
              ? "Multi-agent mode — complex queries engage multiple specialised agents"
              : "Auto-routing — AQAA detects the right agent for your question · Shift+Enter for new line"}
          </p>
        </div>
      </div>
    </div>
  );
}
