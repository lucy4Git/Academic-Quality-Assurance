"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, Brain, ChevronRight, Copy, Pencil, RefreshCw, Square, Sparkles } from "lucide-react";
import { MarkdownMessage } from "@/components/ai/MarkdownMessage";
import { askStream } from "@/lib/api/ai-assistant";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

type PromptItem = { category: string; emoji: string; prompt: string };
type Message = { id: string; role: "user" | "assistant"; content: string; created_at?: string };

const QA_OFFICER_PROMPTS: PromptItem[] = [
  { category: "Evidence", emoji: "📂", prompt: "Review a module or course folder" },
  { category: "Completeness", emoji: "✅", prompt: "Find missing QA evidence" },
  { category: "Assessment", emoji: "📝", prompt: "Review assessment and moderation evidence" },
  { category: "Reporting", emoji: "📋", prompt: "Generate a QA report" },
];
const LECTURER_PROMPTS: PromptItem[] = [
  { category: "Module folder", emoji: "📂", prompt: "Check my module or course folder" },
  { category: "Documents", emoji: "✅", prompt: "Find missing documents" },
  { category: "Assessment", emoji: "📝", prompt: "Review my assessment evidence" },
  { category: "Remediation", emoji: "🔍", prompt: "Help me resolve QA findings" },
];

export function GenericWorkspaceView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const routeSessionId = searchParams.get("session");
  const [activeSessionId, setActiveSessionId] = useState<string | null>(routeSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const prompts = user?.persona === "lecturer" ? LECTURER_PROMPTS : QA_OFFICER_PROMPTS;

  useEffect(() => {
    setActiveSessionId(routeSessionId);
    setMessages([]);
    setError(null);
    if (!routeSessionId) return;
    let cancelled = false;
    void fetch(`/api/proxy/ai-assistant/sessions/${routeSessionId}`, { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) throw new Error(response.status === 404 ? "Conversation not found." : "Could not load this conversation.");
        return response.json() as Promise<{ messages: Message[] }>;
      })
      .then((session) => {
        if (!cancelled) setMessages(session.messages.map((message) => ({ ...message, id: String(message.id) })));
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not load this conversation.");
      });
    return () => { cancelled = true; };
  }, [routeSessionId]);

  const send = async (promptOverride?: string) => {
    const question = (promptOverride ?? query).trim();
    if (!question || isGenerating) return;
    const userMessage: Message = { id: `user-${Date.now()}`, role: "user", content: question, created_at: new Date().toISOString() };
    const assistantId = `assistant-${Date.now()}`;
    setMessages((current) => [...current, userMessage, { id: assistantId, role: "assistant", content: "", created_at: new Date().toISOString() }]);
    setQuery(""); setError(null); setIsGenerating(true);
    const controller = new AbortController(); abortRef.current = controller;
    try {
      for await (const event of askStream({ question, session_id: activeSessionId }, controller.signal)) {
        if (event.type === "token") {
          setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, content: message.content + event.content } : message));
        } else if (event.type === "session") {
          setActiveSessionId(event.session_id);
          router.replace(`/workspace?session=${event.session_id}`);
        } else if (event.type === "error") throw new Error(event.message);
      }
    } catch (reason) {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "AQAA could not complete the response. Please try again.");
      setMessages((current) => current.filter((message) => message.id !== assistantId || message.content.length > 0));
    } finally { abortRef.current = null; setIsGenerating(false); }
  };
  const handleSubmit = (event: FormEvent) => { event.preventDefault(); void send(); };
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); }
  };
  const personaLabel = user?.persona === "lecturer" ? "Lecturer" : "Quality Assurance Officer";
  const retryResponse = (index: number) => {
    for (let candidate = index - 1; candidate >= 0; candidate -= 1) {
      if (messages[candidate].role === "user") { void send(messages[candidate].content); return; }
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        {messages.length === 0 ? (
          <div className="mx-auto max-w-3xl space-y-8 pt-4 text-center sm:pt-8">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-1.5 text-xs font-semibold text-primary"><Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> AQAA Workspace</div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">What would you like to review?</h1>
              <p className="text-muted-foreground">Ask about academic quality, evidence, compliance, and remediation.</p>
            </div>
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Suggested for {personaLabel}</p>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {prompts.map((prompt) => <button key={prompt.prompt} type="button" onClick={() => setQuery(prompt.prompt)} className="group flex items-start gap-2.5 rounded-xl border bg-card/50 p-3 text-left transition hover:bg-card"><span aria-hidden="true">{prompt.emoji}</span><span className="min-w-0 flex-1"><span className="block text-[10.5px] font-semibold uppercase text-primary">{prompt.category}</span><span className="text-sm">{prompt.prompt}</span></span><ChevronRight className="mt-1 h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" /></button>)}
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-6" aria-live="polite">
            {messages.map((message, index) => <article key={message.id} className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}><div className={cn("group max-w-[90%] rounded-2xl px-4 py-3 sm:max-w-[80%]", message.role === "user" ? "bg-primary text-primary-foreground" : "border bg-card")}>{message.role === "assistant" ? <MarkdownMessage content={message.content || "…"} /> : <p className="whitespace-pre-wrap text-sm">{message.content}</p>}<div className={cn("mt-2 flex items-center gap-3 text-xs", message.role === "user" ? "text-primary-foreground/75" : "text-muted-foreground")}>{message.created_at && <time dateTime={message.created_at}>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>}{message.role === "assistant" && message.content && <><button type="button" onClick={() => void navigator.clipboard.writeText(message.content)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100" aria-label="Copy response"><Copy className="h-3.5 w-3.5" /> Copy</button><button type="button" disabled={isGenerating} onClick={() => retryResponse(index)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100 disabled:opacity-40" aria-label="Retry response"><RefreshCw className="h-3.5 w-3.5" /> Retry</button></>}{message.role === "user" && <button type="button" disabled={isGenerating} onClick={() => setQuery(message.content)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100 disabled:opacity-40" aria-label="Edit and resend message"><Pencil className="h-3.5 w-3.5" /> Edit & resend</button>}</div></div></article>)}
          </div>
        )}
      </div>
      <div className="border-t bg-background px-4 py-4 sm:px-6">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
          {error && <p className="mb-2 text-sm text-destructive" role="alert">{error}</p>}
          <div className="flex items-end gap-3 rounded-2xl border-2 bg-card px-4 py-3 focus-within:border-primary/40">
            <Brain className="mb-2 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
            <textarea value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={handleKeyDown} rows={1} placeholder="Ask AQAA anything about academic quality…" className="max-h-40 min-h-10 flex-1 resize-none bg-transparent py-2 outline-none" aria-label="Ask AQAA" disabled={isGenerating} />
            {isGenerating ? <button type="button" onClick={() => abortRef.current?.abort()} className="mb-1 flex h-9 w-9 items-center justify-center rounded-xl bg-muted" aria-label="Stop response"><Square className="h-4 w-4" /></button> : <button type="submit" disabled={!query.trim()} className="mb-1 flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message"><ArrowRight className="h-4 w-4" /></button>}
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">Enter to send · Shift+Enter for a new line</p>
        </form>
      </div>
    </div>
  );
}
