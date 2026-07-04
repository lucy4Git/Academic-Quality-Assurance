"use client";

import { useState, useMemo } from "react";
import {
  Library,
  Search,
  Download,
  Trash2,
  Upload,
  FileText,
  Filter,
} from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import { cn, formatDate } from "@/lib/utils";
import { useEvidence, useDeleteEvidence } from "@/hooks/useEvidence";
import { useAudits } from "@/hooks/useModuleAudits";
import { useRole } from "@/hooks/useRole";
import { evidenceDownloadUrl } from "@/lib/api/evidence";
import { EVIDENCE_CATEGORIES, type AuditEvidence } from "@/types";

function FileSizeLabel({ bytes }: { bytes: number }) {
  if (bytes < 1024) return <>{bytes} B</>;
  if (bytes < 1024 * 1024) return <>{(bytes / 1024).toFixed(1)} KB</>;
  return <>{(bytes / 1024 / 1024).toFixed(1)} MB</>;
}

function MimeBadge({ mime }: { mime: string }) {
  const ext = mime.split("/")[1]?.toUpperCase().slice(0, 4) ?? "FILE";
  return (
    <span className="inline-flex items-center rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
      {ext}
    </span>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-border">
          <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-7 w-16 rounded" />
        </div>
      ))}
    </div>
  );
}

export function FileLibrary() {
  const { isQAOfficer, isSysAdmin, isCoordinator } = useRole();
  const { data: evidence, isLoading, isError, refetch } = useEvidence();
  const { data: audits } = useAudits();
  const deleteMutation = useDeleteEvidence();

  const [search, setSearch] = useState("");
  const [filterCat, setFilterCat] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<AuditEvidence | null>(null);

  const auditMap = useMemo(() => {
    const m = new Map<string, string>();
    audits?.forEach((a) => m.set(a.id, a.academic_year));
    return m;
  }, [audits]);

  const filtered = useMemo(() => {
    if (!evidence) return [];
    let list = [...evidence];
    if (filterCat) list = list.filter((e) => e.evidence_category === filterCat);
    const q = search.trim().toLowerCase();
    if (q)
      list = list.filter(
        (e) =>
          e.original_filename.toLowerCase().includes(q) ||
          e.evidence_category.toLowerCase().includes(q)
      );
    return list;
  }, [evidence, search, filterCat]);

  const canDelete = isSysAdmin || isQAOfficer;
  const canUpload = isCoordinator;

  const cls = "flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm";

  return (
    <>
      <PageHeader
        title="File Library"
        subtitle={evidence ? `${evidence.length} evidence file${evidence.length !== 1 ? "s" : ""}` : undefined}
        actions={
          canUpload ? (
            <div className="flex items-center gap-2">
              <Link href="/files/upload/zip" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
                <Upload className="mr-1.5 h-4 w-4" />
                Bulk ZIP Import
              </Link>
              <Link href="/files/upload" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
                <Upload className="mr-1.5 h-4 w-4" />
                Upload Evidence
              </Link>
            </div>
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by filename or category…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Filter className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <select
          value={filterCat}
          onChange={(e) => setFilterCat(e.target.value)}
          className={cls}
        >
          <option value="">All categories</option>
          {EVIDENCE_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      {isLoading && <TableSkeleton />}
      {isError && <ErrorState message="Failed to load evidence files." onRetry={refetch} />}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Library}
          title={search || filterCat ? "No files match your filters" : "No evidence files yet"}
          description="Upload evidence files against audit checklist items to track compliance."
          action={
            canUpload && !search ? (
              <Link href="/files/upload" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
                <Upload className="mr-1.5 h-4 w-4" />
                Upload Evidence
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="rounded-xl border border-border overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-[1fr_100px_120px_90px_100px] gap-4 px-4 py-2 bg-muted/50 border-b border-border text-xs font-medium uppercase tracking-wide text-muted-foreground hidden sm:grid">
            <span>Filename</span>
            <span>Type</span>
            <span>Category</span>
            <span>Size</span>
            <span>Uploaded</span>
          </div>

          <div className="divide-y divide-border">
            {filtered.map((ev) => {
              const catLabel = EVIDENCE_CATEGORIES.find((c) => c.value === ev.evidence_category)?.label ?? ev.evidence_category;
              return (
                <div
                  key={ev.id}
                  className="grid grid-cols-1 sm:grid-cols-[1fr_100px_120px_90px_100px] gap-2 sm:gap-4 items-center px-4 py-3 hover:bg-muted/30 transition-colors group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{ev.original_filename}</p>
                      {ev.description && (
                        <p className="text-xs text-muted-foreground truncate">{ev.description}</p>
                      )}
                    </div>
                  </div>
                  <MimeBadge mime={ev.mime_type} />
                  <span className="text-xs text-muted-foreground truncate">{catLabel}</span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    <FileSizeLabel bytes={ev.file_size_bytes} />
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      {formatDate(ev.created_at)}
                    </span>
                    <a
                      href={evidenceDownloadUrl(ev.id)}
                      download={ev.original_filename}
                      className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Download"
                    >
                      <Download className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                    </a>
                    {canDelete && (
                      <button
                        onClick={() => setDeleteTarget(ev)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Evidence"
        description={`Are you sure you want to permanently delete "${deleteTarget?.original_filename}"? This cannot be undone.`}
        confirmLabel="Delete"
        isPending={deleteMutation.isPending}
        onConfirm={async () => {
          if (deleteTarget) await deleteMutation.mutateAsync(deleteTarget.id);
          setDeleteTarget(null);
        }}
      />
    </>
  );
}
