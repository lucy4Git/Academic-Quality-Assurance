"use client";

/**
 * ArtifactPanel — Phase D5 Artifact Engine frontend.
 *
 * Renders a right-side panel (desktop), slide-over (tablet), or full-screen
 * (mobile) view of AI-generated artifacts for the current conversation.
 *
 * Features
 * --------
 * - List artifacts for the active conversation
 * - Inline artifact card in message flow (ArtifactCard)
 * - Full-screen preview
 * - Version history
 * - Rename / save / archive / restore
 * - Source trace (evidence, findings, frameworks, assessments links)
 * - Approval state display
 * - Export (JSON / Markdown — only formats the backend actually supports)
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  FileText, ChevronRight, Download, Archive, RotateCcw,
  CheckCircle2, Clock, AlertTriangle, X, History,
  Layers, Link2, Edit2, Check, RefreshCw, Maximize2,
  Minimize2, ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ArtifactBrief {
  id: string;
  artifact_type: string;
  title: string;
  description: string | null;
  status: "draft" | "saved" | "versioned" | "archived" | "deleted";
  approval_status: "not_required" | "pending" | "approved" | "rejected";
  version_number: number;
  conversation_id: string | null;
  institution_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactDetail extends ArtifactBrief {
  content_json: Record<string, unknown> | null;
  rendered_content: string | null;
  source_context: Record<string, unknown> | null;
  source_evidence: string[] | null;
  source_findings: string[] | null;
  source_frameworks: string[] | null;
  source_assessments: string[] | null;
  export_formats: string[];
  parent_artifact_id: string | null;
  message_id: string | null;
}

// ── API helpers ────────────────────────────────────────────────────────────────

const PROXY = "/api/proxy";

async function fetchArtifacts(conversationId: string): Promise<ArtifactBrief[]> {
  const res = await fetch(`${PROXY}/artifacts?conversation_id=${conversationId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error(`Failed to load artifacts: ${res.status}`);
  return res.json();
}

async function fetchArtifact(id: string): Promise<ArtifactDetail> {
  const res = await fetch(`${PROXY}/artifacts/${id}`, { credentials: "include" });
  if (!res.ok) throw new Error(`Artifact not found: ${res.status}`);
  return res.json();
}

async function renameArtifact(id: string, title: string): Promise<ArtifactDetail> {
  const res = await fetch(`${PROXY}/artifacts/${id}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Rename failed");
  return res.json();
}

async function archiveArtifact(id: string): Promise<ArtifactBrief> {
  const res = await fetch(`${PROXY}/artifacts/${id}/archive`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Archive failed");
  return res.json();
}

async function restoreArtifact(id: string): Promise<ArtifactBrief> {
  const res = await fetch(`${PROXY}/artifacts/${id}/restore`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Restore failed");
  return res.json();
}

async function exportArtifact(id: string, format: "json" | "markdown"): Promise<void> {
  const res = await fetch(`${PROXY}/artifacts/${id}/export?format=${format}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `artifact_${id}.${format === "json" ? "json" : "md"}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  module_audit_report: "Module Audit Report",
  programme_compliance_report: "Programme Compliance",
  department_quality_report: "Department Quality",
  faculty_quality_report: "Faculty Quality",
  institutional_quality_report: "Institutional Quality",
  regulatory_readiness_report: "Regulatory Readiness",
  accreditation_evidence_pack: "Accreditation Evidence Pack",
  corrective_action_plan: "Corrective Action Plan",
  risk_register: "Risk Register",
  assessment_alignment_matrix: "Assessment Alignment",
  moderation_report: "Moderation Report",
  executive_briefing: "Executive Briefing",
  qa_meeting_pack: "QA Meeting Pack",
  evidence_checklist: "Evidence Checklist",
  framework_comparison: "Framework Comparison",
  qualification_alignment_report: "Qualification Alignment",
};

function ApprovalBadge({ status }: { status: ArtifactBrief["approval_status"] }) {
  const map = {
    not_required: { label: "—", cls: "bg-muted text-muted-foreground" },
    pending: { label: "Pending review", cls: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400" },
    approved: { label: "Approved", cls: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" },
    rejected: { label: "Rejected", cls: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400" },
  };
  const { label, cls } = map[status] ?? map.not_required;
  if (status === "not_required") return null;
  return (
    <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-semibold", cls)}>
      {label}
    </span>
  );
}

function StatusIcon({ status }: { status: ArtifactBrief["status"] }) {
  if (status === "archived") return <Archive className="h-3.5 w-3.5 text-muted-foreground" />;
  if (status === "saved") return <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />;
  if (status === "versioned") return <History className="h-3.5 w-3.5 text-blue-500" />;
  return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  } catch { return iso; }
}

// ── Inline artifact card (shown in message flow) ───────────────────────────────

export function ArtifactCard({
  artifact,
  onOpen,
}: {
  artifact: ArtifactBrief;
  onOpen: (id: string) => void;
}) {
  return (
    <div className="mt-3 rounded-xl border border-border bg-card/50 p-3 hover:border-blue-300 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="h-4 w-4 text-blue-500 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              {ARTIFACT_TYPE_LABELS[artifact.artifact_type] ?? artifact.artifact_type}
            </p>
            <p className="text-sm font-semibold text-foreground truncate">{artifact.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <StatusIcon status={artifact.status} />
          <ApprovalBadge status={artifact.approval_status} />
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className="text-[10px] text-muted-foreground">v{artifact.version_number} · {formatDate(artifact.created_at)}</span>
        <button
          type="button"
          onClick={() => onOpen(artifact.id)}
          className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Open <ChevronRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

// ── Artifact detail view ───────────────────────────────────────────────────────

function ArtifactDetailView({
  artifactId,
  onClose,
  onRefreshList,
}: {
  artifactId: string;
  onClose: () => void;
  onRefreshList: () => void;
}) {
  const [artifact, setArtifact] = useState<ArtifactDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [fullscreen, setFullscreen] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchArtifact(artifactId);
      setArtifact(data);
      setEditTitle(data.title);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load artifact");
    } finally {
      setLoading(false);
    }
  }, [artifactId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (editing) titleRef.current?.focus(); }, [editing]);

  const handleRename = async () => {
    if (!artifact || editTitle === artifact.title) { setEditing(false); return; }
    try {
      const updated = await renameArtifact(artifact.id, editTitle);
      setArtifact(prev => prev ? { ...prev, title: updated.title } : prev);
      toast.success("Artifact renamed");
      onRefreshList();
    } catch { toast.error("Rename failed"); }
    setEditing(false);
  };

  const handleArchive = async () => {
    if (!artifact) return;
    try {
      await archiveArtifact(artifact.id);
      toast.success("Artifact archived");
      onRefreshList();
      onClose();
    } catch { toast.error("Archive failed"); }
  };

  const handleRestore = async () => {
    if (!artifact) return;
    try {
      await restoreArtifact(artifact.id);
      toast.success("Artifact restored");
      await load();
      onRefreshList();
    } catch { toast.error("Restore failed"); }
  };

  const handleExport = async (format: "json" | "markdown") => {
    if (!artifact) return;
    try {
      await exportArtifact(artifact.id, format);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch { toast.error("Export failed"); }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-12">
      <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
    </div>
  );

  if (error || !artifact) return (
    <div className="p-4 text-sm text-red-500 flex items-center gap-2">
      <AlertTriangle className="h-4 w-4" />
      {error ?? "Artifact not found"}
    </div>
  );

  const isArchived = artifact.status === "archived";

  return (
    <div className={cn(
      "flex flex-col overflow-hidden",
      fullscreen ? "fixed inset-0 z-50 bg-background" : "h-full",
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 px-4 py-3 border-b border-border flex-shrink-0">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-0.5">
            {ARTIFACT_TYPE_LABELS[artifact.artifact_type] ?? artifact.artifact_type}
          </p>
          {editing ? (
            <div className="flex items-center gap-1">
              <input
                ref={titleRef}
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") void handleRename(); if (e.key === "Escape") setEditing(false); }}
                className="flex-1 text-sm font-semibold bg-transparent border-b border-blue-400 focus:outline-none text-foreground"
                aria-label="Edit artifact title"
              />
              <button type="button" onClick={handleRename} className="text-green-500 hover:text-green-600" aria-label="Save title">
                <Check className="h-4 w-4" />
              </button>
              <button type="button" onClick={() => setEditing(false)} className="text-muted-foreground hover:text-foreground" aria-label="Cancel rename">
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="text-sm font-semibold text-foreground hover:text-blue-600 text-left group flex items-center gap-1"
              aria-label="Rename artifact"
            >
              {artifact.title}
              <Edit2 className="h-3 w-3 opacity-0 group-hover:opacity-60 transition-opacity" />
            </button>
          )}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-muted-foreground">v{artifact.version_number}</span>
            <StatusIcon status={artifact.status} />
            <ApprovalBadge status={artifact.approval_status} />
          </div>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            type="button"
            onClick={() => setFullscreen((v) => !v)}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label={fullscreen ? "Exit full screen" : "Full screen"}
          >
            {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Close artifact"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-muted/30 flex-shrink-0 flex-wrap">
        {isArchived ? (
          <button type="button" onClick={handleRestore}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-foreground bg-muted hover:bg-muted/80 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Restore
          </button>
        ) : (
          <button type="button" onClick={handleArchive}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <Archive className="h-3.5 w-3.5" /> Archive
          </button>
        )}
        {/* Export — only JSON and Markdown are verified working */}
        <button type="button" onClick={() => handleExport("json")}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <Download className="h-3.5 w-3.5" /> JSON
        </button>
        <button type="button" onClick={() => handleExport("markdown")}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <Download className="h-3.5 w-3.5" /> Markdown
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {artifact.description && (
          <p className="text-sm text-muted-foreground italic">{artifact.description}</p>
        )}

        {/* Rendered content (markdown) */}
        {artifact.rendered_content ? (
          <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
            {artifact.rendered_content}
          </div>
        ) : artifact.content_json ? (
          <pre className="rounded-lg bg-muted/50 p-3 text-xs overflow-x-auto text-foreground">
            {JSON.stringify(artifact.content_json, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-6">No content</p>
        )}

        {/* Source trace */}
        {(artifact.source_evidence?.length || artifact.source_findings?.length || artifact.source_frameworks?.length) && (
          <div className="border-t border-border pt-3">
            <button
              type="button"
              onClick={() => setShowSources((v) => !v)}
              className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors mb-2"
            >
              <Link2 className="h-3.5 w-3.5" />
              Source trace
              <ChevronDown className={cn("h-3 w-3 transition-transform", showSources && "rotate-180")} />
            </button>
            {showSources && (
              <div className="space-y-2 text-xs text-muted-foreground">
                {artifact.source_evidence?.length ? (
                  <div>
                    <span className="font-semibold text-foreground">Evidence files: </span>
                    {artifact.source_evidence.length} linked
                  </div>
                ) : null}
                {artifact.source_findings?.length ? (
                  <div>
                    <span className="font-semibold text-foreground">Findings: </span>
                    {artifact.source_findings.length} linked
                  </div>
                ) : null}
                {artifact.source_frameworks?.length ? (
                  <div>
                    <span className="font-semibold text-foreground">Frameworks: </span>
                    {artifact.source_frameworks.join(", ")}
                  </div>
                ) : null}
                {artifact.source_assessments?.length ? (
                  <div>
                    <span className="font-semibold text-foreground">Assessments: </span>
                    {artifact.source_assessments.length} linked
                  </div>
                ) : null}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Artifact list (panel sidebar) ─────────────────────────────────────────────

function ArtifactList({
  conversationId,
  selectedId,
  onSelect,
  refreshTick,
}: {
  conversationId: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  refreshTick: number;
}) {
  const [artifacts, setArtifacts] = useState<ArtifactBrief[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchArtifacts(conversationId)
      .then(setArtifacts)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [conversationId, refreshTick]);

  if (loading) return (
    <div className="flex items-center justify-center py-6">
      <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
    </div>
  );

  if (artifacts.length === 0) return (
    <div className="py-6 text-center text-xs text-muted-foreground">
      No artifacts yet — ask the AI to generate a report.
    </div>
  );

  return (
    <div className="space-y-1.5 px-2 py-2">
      {artifacts.map((a) => (
        <button
          key={a.id}
          type="button"
          onClick={() => onSelect(a.id)}
          className={cn(
            "w-full text-left rounded-xl px-3 py-2.5 transition-colors border",
            selectedId === a.id
              ? "border-blue-400 bg-blue-50/50 dark:bg-blue-950/20"
              : "border-transparent hover:border-border hover:bg-muted/50",
          )}
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              <Layers className="h-3.5 w-3.5 text-blue-500 flex-shrink-0" />
              <span className="text-xs font-semibold text-foreground truncate">{a.title}</span>
            </div>
            <StatusIcon status={a.status} />
          </div>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            {ARTIFACT_TYPE_LABELS[a.artifact_type] ?? a.artifact_type} · v{a.version_number}
          </p>
        </button>
      ))}
    </div>
  );
}

// ── Main panel ─────────────────────────────────────────────────────────────────

export function ArtifactPanel({
  conversationId,
  onClose,
}: {
  conversationId: string | null;
  onClose: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const refresh = useCallback(() => setRefreshTick((t) => t + 1), []);

  if (!conversationId) return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-semibold">Artifacts</span>
        </div>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label="Close artifacts panel">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 flex items-center justify-center text-xs text-muted-foreground text-center px-4">
        Start a conversation to generate artifacts.
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-semibold">Artifacts</span>
        </div>
        <div className="flex items-center gap-1">
          <button type="button" onClick={refresh} className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors" aria-label="Refresh artifacts">
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
          {selectedId && (
            <button type="button" onClick={() => setSelectedId(null)} className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors" aria-label="Back to list">
              <ChevronRight className="h-3.5 w-3.5 rotate-180" />
            </button>
          )}
          <button type="button" onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors" aria-label="Close panel">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content: list or detail */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {selectedId ? (
            <motion.div
              key="detail"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              <ArtifactDetailView
                artifactId={selectedId}
                onClose={() => setSelectedId(null)}
                onRefreshList={refresh}
              />
            </motion.div>
          ) : (
            <motion.div
              key="list"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.15 }}
              className="h-full overflow-y-auto"
            >
              <ArtifactList
                conversationId={conversationId}
                selectedId={selectedId}
                onSelect={setSelectedId}
                refreshTick={refreshTick}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
