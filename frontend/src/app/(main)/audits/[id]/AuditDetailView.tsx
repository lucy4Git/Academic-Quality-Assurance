"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  SearchCheck, Pencil, Save, Loader2, Trash2, Paperclip,
  Download, X, Eye, Clock, FileText, Image as ImageIcon, File,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatDateTime } from "@/lib/utils";
import { useAudit, useUpdateAudit, useDeleteAudit } from "@/hooks/useModuleAudits";
import { useAuditEvidence, useDeleteEvidence, useAuditHistory } from "@/hooks/useEvidence";
import { useModule } from "@/hooks/useModules";
import { useRole } from "@/hooks/useRole";
import { evidenceDownloadUrl, evidencePreviewUrl } from "@/lib/api/evidence";
import type {
  AuditChecklistItem, ChecklistItemStatus, ChecklistItemUpdate,
  ModuleAuditStatus, AuditHistory,
} from "@/types";
import {
  CHECKLIST_ITEM_STATUS_LABELS,
  CHECKLIST_ITEM_STATUS_COLOURS,
  MODULE_AUDIT_STATUS_LABELS,
  MODULE_AUDIT_STATUS_COLOURS,
} from "@/types";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: ModuleAuditStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold", MODULE_AUDIT_STATUS_COLOURS[status])}>
      {MODULE_AUDIT_STATUS_LABELS[status]}
    </span>
  );
}

function ComplianceRing({ pct }: { pct: number }) {
  const colour = pct >= 90 ? "text-green-600" : pct >= 70 ? "text-amber-600" : "text-red-600";
  return (
    <div className="flex flex-col items-center gap-1">
      <p className={cn("text-4xl font-bold tabular-nums", colour)}>{pct.toFixed(0)}%</p>
      <p className="text-xs text-muted-foreground">Compliance</p>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between"><Skeleton className="h-8 w-56" /><Skeleton className="h-8 w-20" /></div>
      <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      <Skeleton className="h-96 rounded-xl" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Evidence preview modal
// ---------------------------------------------------------------------------

const IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]);
const TEXT_TYPES = new Set(["text/plain", "text/csv"]);

function PreviewIcon({ mimeType }: { mimeType: string }) {
  if (mimeType === "application/pdf") return <FileText className="h-3.5 w-3.5 text-red-500" />;
  if (IMAGE_TYPES.has(mimeType)) return <ImageIcon className="h-3.5 w-3.5 text-blue-500" />;
  if (TEXT_TYPES.has(mimeType)) return <FileText className="h-3.5 w-3.5 text-slate-500" />;
  return <File className="h-3.5 w-3.5 text-muted-foreground" />;
}

function isPreviewable(mimeType: string): boolean {
  return (
    mimeType === "application/pdf" ||
    IMAGE_TYPES.has(mimeType) ||
    TEXT_TYPES.has(mimeType) ||
    mimeType === "text/html"
  );
}

interface PreviewModalProps {
  evidenceId: string;
  filename: string;
  mimeType: string;
  onClose: () => void;
}

function PreviewModal({ evidenceId, filename, mimeType, onClose }: PreviewModalProps) {
  const url = evidencePreviewUrl(evidenceId);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="relative flex flex-col bg-background rounded-xl shadow-2xl w-[90vw] max-w-4xl h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <p className="text-sm font-medium truncate max-w-[80%]">{filename}</p>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {IMAGE_TYPES.has(mimeType) ? (
            // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
            <img src={url} alt={filename} className="h-full w-full object-contain p-4" />
          ) : (
            <iframe src={url} title={filename} className="h-full w-full border-0" />
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Timeline
// ---------------------------------------------------------------------------

const EVENT_ICONS: Record<string, string> = {
  audit_created: "🎉",
  checklist_updated: "✏️",
  evidence_uploaded: "📎",
  evidence_deleted: "🗑️",
  status_changed: "🔄",
  compliance_changed: "📊",
  notes_updated: "📝",
};

function TimelineSection({ auditId }: { auditId: string }) {
  const { data: history, isLoading } = useAuditHistory(auditId);

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm font-medium flex items-center gap-2"><Clock className="h-4 w-4" /> Audit Timeline</CardTitle></CardHeader>
        <CardContent><div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div></CardContent>
      </Card>
    );
  }

  if (!history || history.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm font-medium flex items-center gap-2"><Clock className="h-4 w-4" /> Audit Timeline</CardTitle></CardHeader>
        <CardContent><p className="text-xs text-muted-foreground">No history events recorded yet.</p></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Clock className="h-4 w-4" /> Audit Timeline
          <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">{history.length}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ol className="relative border-l border-border ml-4">
          {history.map((event) => (
            <li key={event.id} className="mb-4 ml-4">
              <div className="absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full bg-muted ring-2 ring-background text-[10px]">
                {EVENT_ICONS[event.event_type] ?? "•"}
              </div>
              <div className="flex flex-col gap-0.5">
                <p className="text-xs text-foreground">{event.summary}</p>
                <p className="text-[11px] text-muted-foreground">{formatDateTime(event.created_at)}</p>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AuditDetailView({ id }: { id: string }) {
  const router = useRouter();
  const { isCoordinator, isSysAdmin, isQAOfficer } = useRole();
  const { data: audit, isLoading, isError, refetch } = useAudit(id);
  const { data: module } = useModule(audit?.module_id ?? "");
  const { data: auditEvidence } = useAuditEvidence(id);
  const updateMutation = useUpdateAudit(id);
  const deleteMutation = useDeleteAudit();
  const deleteEvidenceMutation = useDeleteEvidence();

  const [editing, setEditing] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [localChecklist, setLocalChecklist] = useState<Record<string, ChecklistItemUpdate>>({});
  const [localNotes, setLocalNotes] = useState<string>("");
  const [preview, setPreview] = useState<{ id: string; filename: string; mimeType: string } | null>(null);

  const canEdit = isCoordinator;
  const canDelete = isSysAdmin || isQAOfficer;

  function startEdit() {
    if (!audit) return;
    setLocalNotes(audit.notes ?? "");
    const init: Record<string, ChecklistItemUpdate> = {};
    audit.checklist_items.forEach((item) => {
      init[item.item_key] = {
        status: item.status,
        comment: item.comment ?? "",
        evidence_required: item.evidence_required,
      };
    });
    setLocalChecklist(init);
    setEditing(true);
  }

  async function saveEdit() {
    await updateMutation.mutateAsync({ notes: localNotes || null, checklist: localChecklist });
    setEditing(false);
  }

  if (isLoading) return <DetailSkeleton />;
  if (isError || !audit) return <ErrorState title="Audit not found" onRetry={() => refetch()} />;

  const statusCls = (s: ChecklistItemStatus) =>
    cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold", CHECKLIST_ITEM_STATUS_COLOURS[s]);

  return (
    <>
      {preview && (
        <PreviewModal
          evidenceId={preview.id}
          filename={preview.filename}
          mimeType={preview.mimeType}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="space-y-6">
        <PageHeader
          title="Module Folder Audit"
          subtitle={module ? `${module.code} — ${module.name} · ${audit.academic_year}` : audit.academic_year}
          actions={
            <div className="flex items-center gap-2">
              {canEdit && !editing && (
                <Button size="sm" variant="outline" onClick={startEdit}>
                  <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit Checklist
                </Button>
              )}
              {editing && (
                <>
                  <Button size="sm" variant="outline" onClick={() => setEditing(false)} disabled={updateMutation.isPending}>
                    Cancel
                  </Button>
                  <Button size="sm" onClick={saveEdit} disabled={updateMutation.isPending}>
                    {updateMutation.isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
                    <Save className="mr-1.5 h-3.5 w-3.5" /> Save
                  </Button>
                </>
              )}
              {canDelete && (
                <Button size="sm" variant="destructive" onClick={() => setShowDelete(true)}>
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Delete
                </Button>
              )}
            </div>
          }
        />

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Status", value: <StatusBadge status={audit.status} /> },
            { label: "Compliance", value: <ComplianceRing pct={audit.compliance_percentage} /> },
            { label: "Compliant", value: <span className="text-2xl font-bold text-green-600">{audit.compliant_count}</span> },
            { label: "Missing", value: <span className="text-2xl font-bold text-red-600">{audit.missing_count}</span> },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-xl border border-border bg-card p-4 flex flex-col gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
              {value}
            </div>
          ))}
        </div>

        {/* Checklist table */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              QA Checklist — {audit.total_items} items
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {audit.checklist_items.map((item) => {
                const local = localChecklist[item.item_key];
                const currentStatus = (editing ? local?.status : item.status) ?? item.status;
                const currentComment = editing ? (local?.comment ?? "") : (item.comment ?? "");
                const itemEvidence = auditEvidence?.filter((e) => e.checklist_item_id === item.id) ?? [];

                return (
                  <div key={item.item_key} className="p-4 flex flex-col gap-3">
                    <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">{item.item_label}</p>
                        {!editing && item.comment && (
                          <p className="text-xs text-muted-foreground mt-1">{item.comment}</p>
                        )}
                        {editing && (
                          <input
                            type="text"
                            value={currentComment}
                            placeholder="Add comment…"
                            onChange={(e) =>
                              setLocalChecklist((prev) => ({
                                ...prev,
                                [item.item_key]: { ...prev[item.item_key], comment: e.target.value },
                              }))
                            }
                            className="mt-1.5 flex h-8 w-full rounded-md border border-input bg-background px-2 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          />
                        )}
                      </div>

                      <div className="flex-shrink-0">
                        {editing ? (
                          <select
                            value={currentStatus}
                            onChange={(e) =>
                              setLocalChecklist((prev) => ({
                                ...prev,
                                [item.item_key]: {
                                  ...prev[item.item_key],
                                  status: e.target.value as ChecklistItemStatus,
                                },
                              }))
                            }
                            className="flex h-8 rounded-md border border-input bg-background px-2 py-1 text-xs"
                          >
                            {(["compliant", "missing", "partial", "not_applicable"] as ChecklistItemStatus[]).map((s) => (
                              <option key={s} value={s}>{CHECKLIST_ITEM_STATUS_LABELS[s]}</option>
                            ))}
                          </select>
                        ) : (
                          <span className={statusCls(item.status)}>
                            {CHECKLIST_ITEM_STATUS_LABELS[item.status]}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Evidence files */}
                    {itemEvidence.length > 0 && (
                      <div className="ml-1 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                          <Paperclip className="h-3 w-3" /> Evidence ({itemEvidence.length})
                        </p>
                        {itemEvidence.map((ev) => (
                          <div key={ev.id} className="flex items-center gap-2 rounded-md bg-muted/40 px-3 py-1.5 text-xs group">
                            <PreviewIcon mimeType={ev.mime_type} />
                            <span className="flex-1 truncate text-foreground">{ev.original_filename}</span>
                            {isPreviewable(ev.mime_type) && (
                              <button
                                onClick={() => setPreview({ id: ev.id, filename: ev.original_filename, mimeType: ev.mime_type })}
                                className="text-muted-foreground hover:text-primary transition-colors"
                                title="Preview"
                              >
                                <Eye className="h-3.5 w-3.5" />
                              </button>
                            )}
                            <a
                              href={evidenceDownloadUrl(ev.id)}
                              download={ev.original_filename}
                              className="text-muted-foreground hover:text-primary transition-colors"
                              title="Download"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </a>
                            {(isSysAdmin || isQAOfficer) && (
                              <button
                                onClick={() => deleteEvidenceMutation.mutate(ev.id)}
                                className="text-muted-foreground hover:text-destructive transition-colors"
                                title="Delete evidence"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Upload link */}
                    {isCoordinator && (
                      <a
                        href={`/files/upload?audit_id=${id}&checklist_item_id=${item.id}&category=${item.item_key}`}
                        className="text-xs text-primary hover:underline flex items-center gap-1 ml-1"
                      >
                        <Paperclip className="h-3 w-3" /> Attach evidence
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Notes */}
        {(audit.notes || editing) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Auditor Notes</CardTitle>
            </CardHeader>
            <CardContent>
              {editing ? (
                <textarea
                  rows={4}
                  value={localNotes}
                  onChange={(e) => setLocalNotes(e.target.value)}
                  placeholder="Add notes…"
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                />
              ) : (
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{audit.notes}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Timeline */}
        <TimelineSection auditId={id} />

        {/* Metadata */}
        <p className="text-xs text-muted-foreground">
          Created {formatDateTime(audit.created_at)} · Last updated {formatDateTime(audit.updated_at)}
        </p>

        <ConfirmDialog
          open={showDelete}
          onOpenChange={setShowDelete}
          title="Delete Audit"
          description="Are you sure you want to permanently delete this audit? This cannot be undone."
          confirmLabel="Delete Audit"
          isPending={deleteMutation.isPending}
          onConfirm={async () => {
            await deleteMutation.mutateAsync(id);
            setShowDelete(false);
            router.push("/audits");
          }}
        />
      </div>
    </>
  );
}
