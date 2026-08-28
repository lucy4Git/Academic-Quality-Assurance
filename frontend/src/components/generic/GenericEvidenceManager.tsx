"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Archive, Download, FileText, FolderPlus, Search, Trash2, Upload } from "lucide-react";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { GenericFile, PersonalWorkspace, genericEvidenceApi } from "@/lib/api/generic-evidence";

const CATEGORIES = [
  ["course_outline", "Module/course guide"], ["learning_outcomes", "Learning outcomes"],
  ["weekly_plan", "Teaching plan/content"], ["assessment_brief", "Assessment"],
  ["assessment_memo", "Memorandum"], ["assessment_rubric", "Marking guide/rubric"],
  ["internal_moderation", "Internal moderation"], ["external_moderation", "External moderation"],
  ["attendance_register", "Attendance"], ["mark_sheet", "Results"], ["other", "Supporting evidence"],
] as const;

function sizeLabel(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function GenericEvidenceManager({ library = false }: { library?: boolean }) {
  const [workspaces, setWorkspaces] = useState<PersonalWorkspace[]>([]);
  const [files, setFiles] = useState<GenericFile[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [moduleName, setModuleName] = useState("");
  const [moduleCode, setModuleCode] = useState("");
  const [category, setCategory] = useState("course_outline");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<GenericFile | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [workspaceItems, fileItems] = await Promise.all([
        genericEvidenceApi.listWorkspaces(), genericEvidenceApi.listFiles(library),
      ]);
      setWorkspaces(workspaceItems); setFiles(fileItems);
      setWorkspaceId((current) => current || workspaceItems[0]?.id || "");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load your evidence.");
    }
  }, [library]);
  useEffect(() => { void load(); }, [load]);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return needle ? files.filter((item) => `${item.original_filename} ${item.category} ${item.description || ""}`.toLowerCase().includes(needle)) : files;
  }, [files, query]);

  const createWorkspace = async (event: FormEvent) => {
    event.preventDefault(); if (!moduleName.trim()) return;
    setBusy(true); setError(null);
    try {
      const created = await genericEvidenceApi.createWorkspace({ module_name: moduleName.trim(), module_code: moduleCode.trim() || undefined });
      setWorkspaces((current) => [created, ...current]); setWorkspaceId(created.id); setModuleName(""); setModuleCode("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create the workspace."); }
    finally { setBusy(false); }
  };

  const upload = async (event: FormEvent) => {
    event.preventDefault(); if (!selectedFile || !workspaceId) return;
    setBusy(true); setError(null);
    try {
      await genericEvidenceApi.upload({ file: selectedFile, workspaceId, category, description, library });
      setSelectedFile(null); setDescription(""); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Upload failed."); }
    finally { setBusy(false); }
  };

  return <div className="mx-auto max-w-5xl space-y-6">
    <header><h1 className="text-3xl font-bold">{library ? "Library" : "Files"}</h1><p className="mt-1 text-muted-foreground">{library ? "Reusable QA references owned by you." : "Evidence stored inside your personal academic-quality workspace."}</p></header>
    {error && <p className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">{error}</p>}
    {workspaces.length === 0 ? <form onSubmit={createWorkspace} className="rounded-xl border bg-card p-5"><div className="mb-4 flex items-center gap-2"><FolderPlus className="h-5 w-5 text-primary"/><h2 className="font-semibold">Create your first module workspace</h2></div><div className="grid gap-3 sm:grid-cols-[1fr_180px_auto]"><label className="text-sm">Module/course name<input value={moduleName} onChange={(e) => setModuleName(e.target.value)} required maxLength={255} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label><label className="text-sm">Code (optional)<input value={moduleCode} onChange={(e) => setModuleCode(e.target.value)} maxLength={50} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label><button disabled={busy} className="self-end rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">Create workspace</button></div></form> : <form onSubmit={upload} className="rounded-xl border bg-card p-5"><div className="mb-4 flex items-center gap-2"><Upload className="h-5 w-5 text-primary"/><h2 className="font-semibold">{library ? "Add a reference" : "Upload evidence"}</h2></div><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Module/course<select value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)} className="mt-1 w-full rounded-lg border bg-background px-3 py-2">{workspaces.map((item) => <option key={item.id} value={item.id}>{item.module_code ? `${item.module_code} — ` : ""}{item.module_name}</option>)}</select></label><label className="text-sm">Evidence type<select value={category} onChange={(e) => setCategory(e.target.value)} className="mt-1 w-full rounded-lg border bg-background px-3 py-2">{CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="text-sm sm:col-span-2">File<input type="file" required accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.png,.jpg,.jpeg" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} className="mt-1 block w-full rounded-lg border bg-background px-3 py-2 text-sm" /></label><label className="text-sm sm:col-span-2">Description (optional)<input value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1000} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label></div><button disabled={busy || !selectedFile} className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">{busy ? "Uploading…" : library ? "Add to Library" : "Upload evidence"}</button></form>}
    <label className="relative block max-w-sm"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"/><span className="sr-only">Search {library ? "Library" : "files"}</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={`Search ${library ? "Library" : "files"}`} className="w-full rounded-lg border bg-background py-2 pl-9 pr-3 text-sm" /></label>
    {visible.length === 0 ? <div className="rounded-xl border border-dashed p-10 text-center text-muted-foreground"><FileText className="mx-auto mb-3 h-8 w-8"/><p>{query ? "No matching items." : library ? "Your Library is empty." : "No evidence files yet."}</p></div> : <div className="divide-y overflow-hidden rounded-xl border bg-card">{visible.map((item) => <div key={item.id} className="flex items-center gap-3 p-4"><FileText className="h-5 w-5 shrink-0 text-primary"/><div className="min-w-0 flex-1"><p className="truncate font-medium">{item.original_filename}</p><p className="text-xs text-muted-foreground">{item.category.replaceAll("_", " ")} · {sizeLabel(item.size_bytes)} · {item.upload_state}</p></div>{!library && <button type="button" onClick={() => void genericEvidenceApi.setLibrary(item.id, !item.is_library_item).then(load)} className="rounded p-2 hover:bg-muted" aria-label={item.is_library_item ? "Remove from Library" : "Add to Library"}><Archive className="h-4 w-4"/></button>}<a href={genericEvidenceApi.downloadUrl(item.id)} className="rounded p-2 hover:bg-muted" aria-label={`Download ${item.original_filename}`}><Download className="h-4 w-4"/></a><button type="button" onClick={() => setDeleteTarget(item)} className="rounded p-2 text-destructive hover:bg-destructive/10" aria-label={`Delete ${item.original_filename}`}><Trash2 className="h-4 w-4"/></button></div>)}</div>}
    <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)} title="Delete file" description={`Delete “${deleteTarget?.original_filename || "this file"}”? This removes its stored content and cannot be undone.`} confirmLabel="Delete" isPending={busy} onConfirm={async () => { if (!deleteTarget) return; setBusy(true); try { await genericEvidenceApi.remove(deleteTarget.id); setDeleteTarget(null); await load(); } finally { setBusy(false); } }} />
  </div>;
}
