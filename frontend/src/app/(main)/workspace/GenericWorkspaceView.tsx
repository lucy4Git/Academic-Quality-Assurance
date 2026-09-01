"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, Brain, ChevronRight, Copy, Paperclip, Pencil, RefreshCw, Save, Square, Sparkles, X } from "lucide-react";
import { MarkdownMessage } from "@/components/ai/MarkdownMessage";
import { askStream, StreamSource } from "@/lib/api/ai-assistant";
import { GenericFile, genericEvidenceApi } from "@/lib/api/generic-evidence";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

type PromptItem = { category: string; emoji: string; prompt: string };
type UploadItem = { key: string; file: File; status: "uploading" | "processing" | "ready" | "error"; fileId?: string; error?: string };
type Message = { id: string; role: "user" | "assistant"; content: string; created_at?: string; sources?: StreamSource[] };

const QA_OFFICER_PROMPTS: PromptItem[] = [
  { category: "Evidence", emoji: "📂", prompt: "Review a module or course folder" },
  { category: "Completeness", emoji: "✅", prompt: "Find missing QA evidence" },
  { category: "Assessment", emoji: "📝", prompt: "Review assessment and moderation evidence" },
  { category: "Reporting", emoji: "📋", prompt: "Generate a QA report" },
  { category: "Credentials", emoji: "🎓", prompt: "Review an academic certificate or credential" },
];
const LECTURER_PROMPTS: PromptItem[] = [
  { category: "Module folder", emoji: "📂", prompt: "Check my module or course folder" },
  { category: "Documents", emoji: "✅", prompt: "Find missing documents" },
  { category: "Assessment", emoji: "📝", prompt: "Review my assessment evidence" },
  { category: "Remediation", emoji: "🔍", prompt: "Help me resolve QA findings" },
  { category: "Credentials", emoji: "🎓", prompt: "Review an academic certificate or credential" },
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
  const [availableFiles, setAvailableFiles] = useState<GenericFile[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [showAttachments, setShowAttachments] = useState(false);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [savingMessageId, setSavingMessageId] = useState<string | null>(null);
  const [reviewingCredential, setReviewingCredential] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const createdSessionRef = useRef<string | null>(null);
  const prompts = user?.persona === "lecturer" ? LECTURER_PROMPTS : QA_OFFICER_PROMPTS;

  useEffect(() => {
    void Promise.all([genericEvidenceApi.listFiles(false), genericEvidenceApi.listWorkspaces()])
      .then(async ([items, workspaces]) => {
        setAvailableFiles(items.filter((item) => item.upload_state === "ready"));
        const workspace = workspaces[0] ?? await genericEvidenceApi.createWorkspace({ module_name: "My QA workspace" });
        setWorkspaceId(workspace.id);
      })
      .catch(() => setAvailableFiles([]));
  }, []);

  const uploadFiles = async (files: File[]) => {
    if (!workspaceId || files.length === 0) return;
    for (const file of files) {
      const key = `${file.name}-${file.size}-${file.lastModified}`;
      setUploads((current) => [...current.filter((item) => item.key !== key), { key, file, status: "uploading" }]);
      try {
        const uploaded = await genericEvidenceApi.upload({ file, workspaceId, category: "course_outline", description: "Attached directly from the AQAA composer.", library: false });
        setUploads((current) => current.map((item) => item.key === key ? { ...item, fileId: uploaded.id, status: uploaded.upload_state === "ready" ? "ready" : "processing" } : item));
        setAvailableFiles((current) => [...current.filter((item) => item.id !== uploaded.id), uploaded]);
        setSelectedFileIds((current) => current.includes(uploaded.id) ? current : [...current, uploaded.id]);
      } catch (reason) {
        setUploads((current) => current.map((item) => item.key === key ? { ...item, status: "error", error: reason instanceof Error ? reason.message : "Upload failed." } : item));
      }
    }
  };

  useEffect(() => {
    if (routeSessionId && createdSessionRef.current === routeSessionId) {
      createdSessionRef.current = null;
      return;
    }
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

  const reviewCredential = async () => {
    const fileId = selectedFileIds[0];
    if (!fileId || reviewingCredential) return;
    setReviewingCredential(true); setError(null);
    try {
      const response = await fetch(`/api/proxy/credentials/${fileId}/review`, { method: "POST", credentials: "include" });
      const report = await response.json() as Record<string, unknown> & { detail?: string; verification_note?: string };
      if (!response.ok) throw new Error(report.detail || "Credential review failed.");
      const field = (name: string) => { const value = report[name] as { value?: string; status?: string; basis?: string } | undefined; return `- **${name.replaceAll("_", " ")}**: ${value?.value || "UNABLE TO DETERMINE"} (${value?.status}; basis: ${value?.basis})`; };
      const content = `## Credential review\n\n${["holder_name", "qualification", "institution", "award_date", "credential_number"].map(field).join("\n")}\n\n- **Authenticity**: ${report.authenticity_status}\n- **Originality**: ${report.originality_status}\n- **Source**: ${report.source_status}\n\n${report.verification_note}`;
      setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content: "Review this academic credential.", created_at: new Date().toISOString() }, { id: `credential-${Date.now()}`, role: "assistant", content, created_at: new Date().toISOString(), sources: [{ entity_key: fileId, title: availableFiles.find((file) => file.id === fileId)?.original_filename || "Owned credential" }] }]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Credential review failed."); }
    finally { setReviewingCredential(false); }
  };
  const send = async (promptOverride?: string) => {
    const question = (promptOverride ?? query).trim();
    if (!question || isGenerating) return;
    const userMessage: Message = { id: `user-${Date.now()}`, role: "user", content: question, created_at: new Date().toISOString() };
    const assistantId = `assistant-${Date.now()}`;
    setMessages((current) => [...current, userMessage, { id: assistantId, role: "assistant", content: "", created_at: new Date().toISOString() }]);
    setQuery(""); setError(null); setIsGenerating(true);
    const controller = new AbortController(); abortRef.current = controller;
    try {
      for await (const event of askStream({ question, session_id: activeSessionId, attached_file_ids: selectedFileIds }, controller.signal)) {
        if (event.type === "token") {
          setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, content: message.content + event.content } : message));
        } else if (event.type === "session") {
          setActiveSessionId(event.session_id);
          createdSessionRef.current = event.session_id;
          router.replace(`/workspace?session=${event.session_id}`);
        } else if (event.type === "sources") {
          setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, sources: event.sources } : message));
        } else if (event.type === "error") throw new Error(event.message);
      }
      setSelectedFileIds([]);
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
  const saveOutput = async (message: Message, index: number) => {
    setSavingMessageId(message.id); setError(null);
    const question = [...messages.slice(0, index)].reverse().find((item) => item.role === "user")?.content;
    try {
      const response = await fetch("/api/proxy/artifacts", {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          artifact_type: "qa_review",
          title: (question || "AQAA QA review").slice(0, 120),
          description: "Saved from the personal AQAA conversation workspace.",
          rendered_content: message.content,
          conversation_id: activeSessionId,
          source_evidence: message.sources?.map((source) => source.entity_key).filter(Boolean) ?? [],
        }),
      });
      if (!response.ok) throw new Error("Could not save this output.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save this output."); }
    finally { setSavingMessageId(null); }
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
            {messages.map((message, index) => <article key={message.id} className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}><div className={cn("group max-w-[90%] rounded-2xl px-4 py-3 sm:max-w-[80%]", message.role === "user" ? "bg-primary text-primary-foreground" : "border bg-card")}>{message.role === "assistant" ? <MarkdownMessage content={message.content || "…"} /> : <p className="whitespace-pre-wrap text-sm">{message.content}</p>}{message.role === "assistant" && message.sources && message.sources.length > 0 && <div className="mt-3 border-t pt-2"><p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Sources</p><div className="flex flex-wrap gap-1.5">{message.sources.map((source, sourceIndex) => <span key={`${source.entity_key || source.title}-${sourceIndex}`} className="rounded-full border bg-muted/50 px-2 py-1 text-xs text-muted-foreground">{source.source_document || source.title || "Attached evidence"}</span>)}</div></div>}<div className={cn("mt-2 flex items-center gap-3 text-xs", message.role === "user" ? "text-primary-foreground/75" : "text-muted-foreground")}>{message.created_at && <time dateTime={message.created_at}>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>}{message.role === "assistant" && message.content && <><button type="button" onClick={() => void navigator.clipboard.writeText(message.content)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100" aria-label="Copy response"><Copy className="h-3.5 w-3.5" /> Copy</button><button type="button" disabled={isGenerating} onClick={() => retryResponse(index)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100 disabled:opacity-40" aria-label="Retry response"><RefreshCw className="h-3.5 w-3.5" /> Retry</button></>}{message.role === "user" && <button type="button" disabled={isGenerating} onClick={() => setQuery(message.content)} className="inline-flex items-center gap-1 opacity-0 transition group-hover:opacity-100 focus:opacity-100 disabled:opacity-40" aria-label="Edit and resend message"><Pencil className="h-3.5 w-3.5" /> Edit & resend</button>}</div></div></article>)}
          </div>
        )}
      </div>
      <div className="border-t bg-background px-4 py-4 sm:px-6">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void uploadFiles(Array.from(event.dataTransfer.files)); }}>
          {error && <p className="mb-2 text-sm text-destructive" role="alert">{error}</p>}
          <input ref={fileInputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.pptx,.txt" className="sr-only" onChange={(event) => { void uploadFiles(Array.from(event.target.files ?? [])); event.currentTarget.value = ""; }} />
          {uploads.length > 0 && <div className="mb-2 space-y-1 rounded-xl border bg-card p-2" aria-live="polite">{uploads.map((item) => <div key={item.key} className="flex min-h-10 items-center gap-2 rounded-lg px-2 text-xs"><span className="min-w-0 flex-1 truncate">{item.file.name}</span><span className={item.status === "error" ? "text-destructive" : "text-muted-foreground"}>{item.status === "uploading" ? "Uploading…" : item.status === "processing" ? "Processing…" : item.status === "ready" ? "Ready" : item.error}</span>{item.status === "error" && <button type="button" className="font-medium text-primary" onClick={() => void uploadFiles([item.file])}>Retry</button>}<button type="button" aria-label={`Remove ${item.file.name}`} onClick={() => { setUploads((current) => current.filter((value) => value.key !== item.key)); if (item.fileId) setSelectedFileIds((current) => current.filter((id) => id !== item.fileId)); }}><X className="h-3.5 w-3.5" /></button></div>)}</div>}
          {showAttachments && <div className="mb-2 rounded-xl border bg-card p-3"><div className="mb-2 flex items-center justify-between"><p className="text-sm font-medium">Attach owned evidence</p><button type="button" onClick={() => setShowAttachments(false)} aria-label="Close attachment picker"><X className="h-4 w-4" /></button></div>{availableFiles.length === 0 ? <p className="text-sm text-muted-foreground">Upload a processed evidence file from Files first.</p> : <div className="max-h-36 space-y-1 overflow-y-auto">{availableFiles.map((file) => <label key={file.id} className="flex cursor-pointer items-center gap-2 rounded p-2 text-sm hover:bg-muted"><input type="checkbox" checked={selectedFileIds.includes(file.id)} onChange={(event) => setSelectedFileIds((current) => event.target.checked ? [...current, file.id] : current.filter((id) => id !== file.id))} /><span className="truncate">{file.original_filename}</span></label>)}</div>}</div>}
<button type="button" disabled={reviewingCredential} onClick={() => void reviewCredential()} className="mb-2 inline-flex min-h-10 items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50">🎓 {reviewingCredential ? "Reviewing credential…" : "Review selected credential"}</button>
          {selectedFileIds.length > 0 && <div className="mb-2 flex flex-wrap gap-1.5">{selectedFileIds.map((id) => { const file = availableFiles.find((item) => item.id === id); return <span key={id} className="inline-flex items-center gap-1 rounded-full border bg-muted px-2 py-1 text-xs">{file?.original_filename || "Evidence"}<button type="button" onClick={() => setSelectedFileIds((current) => current.filter((value) => value !== id))} aria-label={`Remove ${file?.original_filename || "attachment"}`}><X className="h-3 w-3" /></button></span>; })}</div>}
          {(() => {
            const latestIndex = messages.findLastIndex((message) => message.role === "assistant" && !!message.content);
            const latest = latestIndex >= 0 ? messages[latestIndex] : null;
            return latest ? <div className="mb-2 flex justify-end"><button type="button" disabled={savingMessageId === latest.id} onClick={() => void saveOutput(latest, latestIndex)} className="inline-flex min-h-10 items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"><Save className="h-4 w-4" />{savingMessageId === latest.id ? "Saving…" : "Save latest response"}</button></div> : null;
          })()}
          <div className="flex items-end gap-3 rounded-2xl border-2 bg-card px-4 py-3 focus-within:border-primary/40">
            <Brain className="mb-2 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isGenerating || !workspaceId} className="mb-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl hover:bg-muted disabled:opacity-40" aria-label="Attach files from this device"><Paperclip className="h-4 w-4" /></button>
            <textarea value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={handleKeyDown} rows={1} placeholder="Ask AQAA anything about academic quality…" className="max-h-40 min-h-10 flex-1 resize-none bg-transparent py-2 outline-none" aria-label="Ask AQAA" disabled={isGenerating} />
            {isGenerating ? <button type="button" onClick={() => abortRef.current?.abort()} className="mb-1 flex h-9 w-9 items-center justify-center rounded-xl bg-muted" aria-label="Stop response"><Square className="h-4 w-4" /></button> : <button type="submit" disabled={!query.trim()} className="mb-1 flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message"><ArrowRight className="h-4 w-4" /></button>}
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">Enter to send · Shift+Enter for a new line</p>
        </form>
      </div>
    </div>
  );
}
