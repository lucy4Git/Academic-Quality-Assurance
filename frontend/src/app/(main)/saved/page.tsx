"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, FileText, Search, Trash2, X } from "lucide-react";
import { MarkdownMessage } from "@/components/ai/MarkdownMessage";

type Output = { id: string; artifact_type: string; title: string; description: string | null; status: string; version_number: number; created_at: string; rendered_content?: string | null };

export default function SavedPage() {
  const [items, setItems] = useState<Output[]>([]);
  const [selected, setSelected] = useState<Output | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    const response = await fetch("/api/proxy/artifacts", { credentials: "include" });
    if (!response.ok) throw new Error("Could not load Saved Outputs.");
    setItems(await response.json());
  }, []);
  useEffect(() => { void load().catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load Saved Outputs.")); }, [load]);
  const visible = useMemo(() => items.filter((item) => `${item.title} ${item.description ?? ""} ${item.artifact_type}`.toLowerCase().includes(query.toLowerCase())), [items, query]);
  const open = async (id: string) => {
    const response = await fetch(`/api/proxy/artifacts/${id}`, { credentials: "include" });
    if (!response.ok) { setError("This Saved Output is unavailable."); return; }
    setSelected(await response.json());
  };
  const remove = async (id: string) => {
    if (!window.confirm("Delete this Saved Output? This cannot be undone.")) return;
    const response = await fetch(`/api/proxy/artifacts/${id}`, { method: "DELETE", credentials: "include" });
    if (!response.ok) { setError("Could not delete this Saved Output."); return; }
    setSelected(null); await load();
  };
  return <div className="mx-auto max-w-5xl space-y-6">
    <header><h1 className="text-3xl font-bold">Saved Outputs</h1><p className="mt-1 text-muted-foreground">Reusable QA reports, reviews, finding summaries, and remediation plans owned by you.</p></header>
    {error && <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
    <label className="relative block max-w-md"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"/><span className="sr-only">Search Saved Outputs</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search Saved Outputs" className="w-full rounded-xl border bg-background py-2.5 pl-9 pr-3"/></label>
    {visible.length === 0 ? <div className="rounded-2xl border border-dashed p-12 text-center text-muted-foreground"><FileText className="mx-auto mb-3 h-9 w-9"/><p>{query ? "No matching Saved Outputs." : "No Saved Outputs yet. Ask AQAA to generate a report, review, or remediation plan."}</p></div> : <div className="grid gap-3 sm:grid-cols-2">{visible.map((item) => <article key={item.id} className="rounded-2xl border bg-card p-4"><p className="text-xs font-semibold uppercase tracking-wide text-primary">{item.artifact_type.replaceAll("_", " ")}</p><button type="button" onClick={() => void open(item.id)} className="mt-1 text-left text-lg font-semibold hover:text-primary">{item.title}</button><p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{item.description || `Version ${item.version_number}`}</p><div className="mt-4 flex items-center justify-between text-xs text-muted-foreground"><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleDateString()}</time><div className="flex gap-1"><a href={`/api/proxy/artifacts/${item.id}/export?format=markdown`} className="rounded-lg p-2 hover:bg-muted" aria-label={`Export ${item.title}`}><Download className="h-4 w-4"/></a><button type="button" onClick={() => void remove(item.id)} className="rounded-lg p-2 text-destructive hover:bg-destructive/10" aria-label={`Delete ${item.title}`}><Trash2 className="h-4 w-4"/></button></div></div></article>)}</div>}
    {selected && <div className="fixed inset-0 z-50 flex items-end bg-black/40 sm:items-center sm:justify-center" role="dialog" aria-modal="true" aria-labelledby="saved-output-title"><div className="max-h-[92vh] w-full overflow-y-auto rounded-t-2xl bg-background p-5 sm:max-w-3xl sm:rounded-2xl"><div className="mb-5 flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-primary">{selected.artifact_type.replaceAll("_", " ")}</p><h2 id="saved-output-title" className="text-2xl font-bold">{selected.title}</h2></div><button type="button" onClick={() => setSelected(null)} className="rounded-lg p-2 hover:bg-muted" aria-label="Close Saved Output"><X className="h-5 w-5"/></button></div>{selected.rendered_content ? <MarkdownMessage content={selected.rendered_content}/> : <p className="text-muted-foreground">No rendered content is available.</p>}</div></div>}
  </div>;
}
