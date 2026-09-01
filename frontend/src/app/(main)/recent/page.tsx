"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Archive, MessageSquare, MoreHorizontal, Pencil, Pin, RotateCcw, Search, Trash2 } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { ChatSessionSummary, conversationApi } from "@/lib/api/ai-assistant";

export default function RecentPage() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [archived, setArchived] = useState(false);
  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void conversationApi.list(archived)
      .then((items) => { if (!cancelled) setSessions(items); })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not load recent conversations.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [archived]);
  useEffect(load, [load]);

  const run = async (action: () => Promise<unknown>) => {
    try { setError(null); await action(); load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Conversation action failed."); }
  };
  const submitRename = (event: FormEvent, id: string) => {
    event.preventDefault();
    const next = title.trim();
    if (!next) return;
    void run(() => conversationApi.rename(id, next));
    setEditingId(null);
  };
  const visibleSessions = query.trim()
    ? sessions.filter((session) => (session.title || "Untitled conversation").toLowerCase().includes(query.trim().toLowerCase()))
    : sessions;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div><h1 className="text-3xl font-bold">Recent</h1><p className="mt-1 text-muted-foreground">Continue and manage your AQAA conversations.</p></div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" /><span className="sr-only">Search conversations</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search conversations" className="w-full rounded-lg border bg-background py-2 pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary" /></label>
        <div className="flex rounded-lg border p-1" aria-label="Conversation status"><button type="button" onClick={() => setArchived(false)} className={`rounded-md px-3 py-1.5 text-sm ${!archived ? "bg-primary text-primary-foreground" : ""}`}>Active</button><button type="button" onClick={() => setArchived(true)} className={`rounded-md px-3 py-1.5 text-sm ${archived ? "bg-primary text-primary-foreground" : ""}`}>Archived</button></div>
      </div>
      {loading && <p className="text-sm text-muted-foreground">Loading conversations…</p>}
      {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
      {!loading && !error && visibleSessions.length === 0 && <div className="rounded-xl border border-dashed p-8 text-center"><MessageSquare className="mx-auto mb-3 h-8 w-8 text-muted-foreground" /><p className="font-medium">{query ? "No matching conversations" : archived ? "No archived conversations" : "No conversations yet"}</p>{!archived && !query && <Link href="/workspace" className="mt-2 inline-block text-sm text-primary hover:underline">Start a new conversation</Link>}</div>}
      <div className="divide-y rounded-xl border bg-card">
        {visibleSessions.map((session) => <div key={session.id} className="flex items-center gap-3 p-4"><MessageSquare className="h-5 w-5 shrink-0 text-primary" /><div className="min-w-0 flex-1">{editingId === session.id ? <form onSubmit={(event) => submitRename(event, session.id)} className="flex gap-2"><label className="sr-only" htmlFor={`rename-${session.id}`}>Conversation title</label><input id={`rename-${session.id}`} autoFocus value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} className="min-w-0 flex-1 rounded border px-2 py-1 text-sm" /><button className="text-sm text-primary" type="submit">Save</button></form> : <Link href={`/workspace?session=${session.id}`} className="block rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"><span className="block truncate font-medium">{session.title || "Untitled conversation"}</span><span className="text-xs text-muted-foreground">{session.message_count} messages · {new Date(session.created_at).toLocaleString()}</span></Link>}</div><DropdownMenu><DropdownMenuTrigger aria-label={`Actions for ${session.title || "conversation"}`} className="rounded p-2 hover:bg-muted"><MoreHorizontal className="h-4 w-4" /></DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuItem onClick={() => { setEditingId(session.id); setTitle(session.title || ""); }}><Pencil className="mr-2 h-4 w-4" />Rename</DropdownMenuItem><DropdownMenuItem onClick={() => void run(() => conversationApi.pin(session.id))}><Pin className="mr-2 h-4 w-4" />{session.is_pinned ? "Unpin" : "Pin"}</DropdownMenuItem><DropdownMenuItem onClick={() => void run(() => conversationApi.archive(session.id))}>{archived ? <RotateCcw className="mr-2 h-4 w-4" /> : <Archive className="mr-2 h-4 w-4" />}{archived ? "Restore" : "Archive"}</DropdownMenuItem><DropdownMenuItem variant="destructive" onClick={() => { if (window.confirm("Delete this conversation? This cannot be undone.")) void run(() => conversationApi.remove(session.id)); }}><Trash2 className="mr-2 h-4 w-4" />Delete</DropdownMenuItem></DropdownMenuContent></DropdownMenu></div>)}
      </div>
    </div>
  );
}
