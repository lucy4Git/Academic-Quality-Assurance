"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import {
  useCurrentInstitution,
  useInstitutions,
} from "@/hooks/useInstitutions";
import {
  useAsk,
  useAgentModes,
  useSuggestedPrompts,
  useCreateSession,
  useChatSession,
  useChatSessions,
  useDeleteSession,
  useAgentRouter,
  type AgentRouterResponse,
} from "@/hooks/useAiAssistant";
import type { AskResponse, SourceChunk, ChatMessageBrief } from "@/types/ai-assistant";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DevModeNotice() {
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <strong>Development mode:</strong> Responses use hash-based placeholder embeddings.
      Configure <code className="rounded bg-amber-100 px-1">AI_PROVIDER</code> in{" "}
      <code className="rounded bg-amber-100 px-1">backend/.env</code> to enable real AI.
    </div>
  );
}

function ProviderBadge({
  provider,
  model,
}: {
  provider: string;
  model: string;
}) {
  const colour =
    provider === "openai"
      ? "bg-green-100 text-green-700"
      : provider === "anthropic"
      ? "bg-purple-100 text-purple-700"
      : provider === "ollama"
      ? "bg-blue-100 text-blue-700"
      : "bg-gray-100 text-gray-500";

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colour}`}>
      {provider} · {model}
    </span>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour =
    pct >= 70
      ? "bg-green-100 text-green-700"
      : pct >= 40
      ? "bg-yellow-100 text-yellow-700"
      : "bg-red-100 text-red-600";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colour}`}>
      {pct}% confidence
    </span>
  );
}

function SourceCard({ source }: { source: SourceChunk }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="inline-block rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">
            {source.entity_type}
          </span>
          <span className="font-medium text-gray-900">{source.title || source.entity_key}</span>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="shrink-0 text-xs text-blue-600 hover:underline"
        >
          {expanded ? "Hide" : "Show"}
        </button>
      </div>
      {expanded && (
        <p className="mt-2 text-gray-600 leading-relaxed whitespace-pre-wrap">{source.text}</p>
      )}
      <div className="mt-1 flex flex-wrap gap-3 text-xs text-gray-400">
        <span>Source: {source.source_document}</span>
        <span>Relevance: {(source.relevance_score * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: AskResponse;
  routerResult?: AgentRouterResponse;
}

// ---------------------------------------------------------------------------
// Session sidebar
// ---------------------------------------------------------------------------

function SessionSidebar({
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
    <div className="w-56 shrink-0 border-r border-gray-200 bg-gray-50 flex flex-col">
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onNew}
          className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + New chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {!sessions || sessions.length === 0 ? (
          <p className="text-xs text-gray-400 text-center mt-4">No sessions yet</p>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className={`group rounded-lg px-3 py-2 cursor-pointer flex items-center justify-between gap-1 ${
                s.id === activeSessionId
                  ? "bg-blue-100 text-blue-900"
                  : "hover:bg-gray-100 text-gray-700"
              }`}
              onClick={() => onSelect(s.id)}
            >
              <div className="min-w-0">
                <p className="text-xs font-medium truncate">
                  {s.title || s.mode.replace(/_/g, " ")}
                </p>
                <p className="text-xs text-gray-400">{s.message_count} messages</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(s.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-xs shrink-0"
                title="Delete session"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function AiAssistantView() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "system_admin";
  const queryClient = useQueryClient();
  const { data: currentInstitution } = useCurrentInstitution();
  const { data: institutions } = useInstitutions();

  const [institutionCode, setInstitutionCode] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState("qa_assistant");
  const [detectedIntent, setDetectedIntent] = useState<string | null>(null);
  const [showModeOverride, setShowModeOverride] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: agentModes } = useAgentModes();
  const { data: suggestedData } = useSuggestedPrompts(institutionCode || undefined);
  const { data: sessionDetail } = useChatSession(activeSessionId);

  const ask = useAsk();
  const agentRouter = useAgentRouter();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();

  useEffect(() => {
    if (isAdmin) return;

    setInstitutionCode(currentInstitution?.code ?? "");
    setActiveSessionId(null);
    setMessages([]);
  }, [currentInstitution?.code, isAdmin, user?.id]);

  // Load session messages when switching sessions
  useEffect(() => {
    if (sessionDetail) {
      const loaded: ChatMessage[] = sessionDetail.messages.map((m: ChatMessageBrief) => ({
        id: m.id,
        role: m.role,
        content: m.content,
      }));
      setMessages(loaded);
    }
  }, [sessionDetail]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewSession = useCallback(async () => {
    try {
      const session = await createSession.mutateAsync({
        mode: selectedMode,
        institution_code: institutionCode || undefined,
      });
      setActiveSessionId(session.id);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    } catch {
      // silently allow stateless use
    }
  }, [createSession, selectedMode, institutionCode, queryClient]);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      await deleteSession.mutateAsync(id);
      if (id === activeSessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    [deleteSession, activeSessionId, queryClient]
  );

  const handleSubmit = useCallback(
    async (question: string) => {
      if (!question.trim()) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      // Auto-detect intent via agent router before asking
      let routerResult: AgentRouterResponse | undefined;
      let effectiveMode = selectedMode;
      try {
        routerResult = await agentRouter.mutateAsync(question);
        setDetectedIntent(routerResult.intent);
        if (!showModeOverride) {
          effectiveMode = routerResult.agent_mode;
          setSelectedMode(routerResult.agent_mode);
        }
      } catch {
        // Router failure is non-fatal — proceed with current mode
      }

      try {
        const result = await ask.mutateAsync({
          question,
          institution_code: institutionCode || null,
          context_limit: 5,
          mode: effectiveMode,
          session_id: activeSessionId,
        });

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          response: result,
          routerResult,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (activeSessionId) {
          queryClient.invalidateQueries({ queryKey: ["chat-session", activeSessionId] });
          queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "An error occurred. Please try again.",
          },
        ]);
      }
    },
    [ask, agentRouter, institutionCode, selectedMode, showModeOverride, activeSessionId, queryClient]
  );

  const handleRegenerate = useCallback(() => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) {
      setMessages((prev) => prev.slice(0, -1)); // remove last assistant msg
      handleSubmit(lastUserMsg.content);
    }
  }, [messages, handleSubmit]);

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setActiveSessionId(null);
  }, []);

  const lastResponse = messages.filter((m) => m.role === "assistant" && m.response).at(-1)
    ?.response;
  const isDevMode = lastResponse?.is_placeholder_mode ?? true;

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Session sidebar */}
      <SessionSidebar
        activeSessionId={activeSessionId}
        onSelect={(id) => {
          setActiveSessionId(id);
          setMessages([]);
        }}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
      />

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-gray-900">AI QA Assistant</h1>
            {lastResponse && (
              <ProviderBadge provider={lastResponse.provider} model={lastResponse.model} />
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Detected intent badge */}
            {detectedIntent && !showModeOverride && (
              <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-medium text-indigo-700">
                Auto: {detectedIntent.replace(/_/g, " ")}
              </span>
            )}

            {/* Advanced override toggle */}
            <button
              onClick={() => setShowModeOverride((v) => !v)}
              className={`rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                showModeOverride
                  ? "border-indigo-400 bg-indigo-50 text-indigo-700"
                  : "border-gray-300 text-gray-500 hover:bg-gray-50"
              }`}
              title="Override automatic agent selection"
            >
              {showModeOverride ? "Override on" : "Override"}
            </button>

            {/* Mode selector — only shown when override is active */}
            {showModeOverride && (
              <select
                value={selectedMode}
                onChange={(e) => setSelectedMode(e.target.value)}
                className="rounded-md border border-indigo-300 bg-white px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {agentModes
                  ? agentModes.map((m) => (
                      <option key={m.mode} value={m.mode}>
                        {m.label}
                      </option>
                    ))
                  : [
                      { mode: "qa_assistant", label: "QA Assistant" },
                      { mode: "audit_assistant", label: "Audit Assistant" },
                      { mode: "policy_assistant", label: "Policy Assistant" },
                      { mode: "evidence_assistant", label: "Evidence Assistant" },
                      { mode: "accreditation_assistant", label: "Accreditation Assistant" },
                      { mode: "qualification_assistant", label: "Qualification Assistant" },
                      { mode: "reporting_assistant", label: "Reporting Assistant" },
                    ].map((m) => (
                      <option key={m.mode} value={m.mode}>
                        {m.label}
                      </option>
                    ))}
              </select>
            )}

            {/* Institution selector (admin only) */}
            {isAdmin && (
              <select
                value={institutionCode}
                onChange={(e) => setInstitutionCode(e.target.value)}
                className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select institution…</option>
                {institutions?.map((institution) => (
                  <option key={institution.id} value={institution.code}>
                    {institution.code} — {institution.name}
                  </option>
                ))}
              </select>
            )}

            {messages.length > 0 && (
              <>
                <button
                  onClick={handleRegenerate}
                  disabled={ask.isPending}
                  className="rounded-md border border-gray-300 px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                  title="Regenerate last response"
                >
                  ↻ Regenerate
                </button>
                <button
                  onClick={handleClearChat}
                  className="rounded-md border border-gray-300 px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
                  title="Clear chat"
                >
                  ✕ Clear
                </button>
              </>
            )}
          </div>
        </div>

        {/* Dev mode notice */}
        {isDevMode && messages.length > 0 && (
          <div className="px-6 pt-3">
            <DevModeNotice />
          </div>
        )}

        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* Suggested prompts (shown only when chat is empty) */}
          {messages.length === 0 && suggestedData && suggestedData.prompts.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                Suggested questions
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestedData.prompts.slice(0, 6).map((p, i) => (
                  <button
                    key={i}
                    onClick={() => handleSubmit(p.prompt)}
                    className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-left text-sm text-gray-700 hover:border-blue-400 hover:bg-blue-50 transition-colors"
                  >
                    <span className="text-xs text-gray-400 block mb-0.5">{p.category}</span>
                    {p.prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                {msg.response && (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <ConfidenceBadge score={msg.response.confidence_score} />
                    <span className="text-xs text-gray-400">
                      {msg.response.query_mode.replace(/_/g, " ")}
                    </span>
                  </div>
                )}

                {/* Sources */}
                {msg.response && msg.response.sources.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs font-semibold text-gray-500">
                      Sources ({msg.response.sources.length})
                    </p>
                    {msg.response.sources.map((src, j) => (
                      <SourceCard key={j} source={src} />
                    ))}
                  </div>
                )}

                {/* Router suggested next actions */}
                {msg.routerResult && msg.routerResult.suggested_next_actions.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-500 mb-1">Suggested actions</p>
                    <ul className="space-y-0.5">
                      {msg.routerResult.suggested_next_actions.map((a, j) => (
                        <li key={j} className="text-xs text-gray-600 flex items-start gap-1">
                          <span className="text-blue-500 shrink-0">›</span>
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Suggested follow-ups from router */}
                {msg.routerResult && msg.routerResult.follow_up_questions.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-500 mb-1">Follow-up questions</p>
                    <div className="flex flex-wrap gap-1">
                      {msg.routerResult.follow_up_questions.map((q, j) => (
                        <button
                          key={j}
                          onClick={() => handleSubmit(q)}
                          className="rounded-full border border-gray-300 bg-gray-50 px-2 py-1 text-xs text-gray-600 hover:border-blue-400 hover:bg-blue-50 transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggested actions from the mode */}
                {msg.response && msg.response.suggested_followups.length > 0 && !msg.routerResult && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-500 mb-1">Follow-up questions</p>
                    <div className="flex flex-wrap gap-1">
                      {msg.response.suggested_followups.map((q, j) => (
                        <button
                          key={j}
                          onClick={() => handleSubmit(q)}
                          className="rounded-full border border-gray-300 bg-gray-50 px-2 py-1 text-xs text-gray-600 hover:border-blue-400 hover:bg-blue-50 transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {ask.isPending && (
            <div className="flex justify-start">
              <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-400">
                Thinking…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(input);
                }
              }}
              placeholder="Ask about programmes, compliance, audits, evidence…"
              disabled={ask.isPending || (isAdmin && !institutionCode)}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={() => handleSubmit(input)}
              disabled={ask.isPending || !input.trim() || (isAdmin && !institutionCode)}
              className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Ask
            </button>
          </div>
          <p className="mt-1.5 text-xs text-gray-400">
            {showModeOverride
              ? `Manual mode: ${selectedMode.replace(/_/g, " ")}`
              : detectedIntent
              ? `Auto-detected: ${detectedIntent.replace(/_/g, " ")} · mode: ${selectedMode.replace(/_/g, " ")}`
              : "Mode auto-detected from your question"}
            {activeSessionId ? " · saving to session" : ""}
          </p>
        </div>
      </div>
    </div>
  );
}
