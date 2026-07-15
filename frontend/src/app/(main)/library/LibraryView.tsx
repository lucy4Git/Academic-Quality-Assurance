"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Library,
  Search,
  FileText,
  Shield,
  Upload,
  Download,
  BookOpen,
  CheckCircle2,
  Clock,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import { cn, formatDate } from "@/lib/utils";
import { useEvidence } from "@/hooks/useEvidence";
import { useRole } from "@/hooks/useRole";
import { evidenceDownloadUrl } from "@/lib/api/evidence";
import { listFrameworks, type QualityFramework } from "@/lib/api/regulatoryFramework";
import { EVIDENCE_CATEGORIES, type AuditEvidence } from "@/types";

// ---------------------------------------------------------------------------
// Tab types
// ---------------------------------------------------------------------------

type Tab = "evidence" | "frameworks";

// ---------------------------------------------------------------------------
// Source status badge
// ---------------------------------------------------------------------------

function SourceStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    verified: {
      label: "Verified",
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
    },
    pending_review: {
      label: "Pending Review",
      icon: <Clock className="h-3 w-3" />,
      cls: "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800",
    },
    draft: {
      label: "Draft",
      icon: <AlertCircle className="h-3 w-3" />,
      cls: "bg-muted text-muted-foreground border-border",
    },
  };
  const cfg = map[status] ?? { label: status, icon: null, cls: "bg-muted text-muted-foreground border-border" };
  return (
    <span className={cn("inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium", cfg.cls)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Evidence tab
// ---------------------------------------------------------------------------

function EvidenceList({ search }: { search: string }) {
  const { data: evidence, isLoading, isError, refetch } = useEvidence();
  const { isCoordinator } = useRole();

  const filtered = useMemo(() => {
    if (!evidence) return [];
    const q = search.trim().toLowerCase();
    if (!q) return evidence;
    return evidence.filter(
      (e) =>
        e.original_filename.toLowerCase().includes(q) ||
        e.evidence_category.toLowerCase().includes(q)
    );
  }, [evidence, search]);

  const categoryLabel = (cat: string) =>
    EVIDENCE_CATEGORIES.find((c) => c.value === cat)?.label ?? cat;

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-border">
            <Skeleton className="h-8 w-8 rounded flex-shrink-0" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-32" />
            </div>
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-7 w-16 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) return <ErrorState message="Failed to load evidence files." onRetry={refetch} />;

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title={search ? "No files match your search" : "No evidence files yet"}
        description="Evidence files are uploaded against audit checklist items."
        action={
          isCoordinator && !search ? (
            <Link href="/files/upload" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
              <Upload className="mr-1.5 h-4 w-4" />
              Upload Evidence
            </Link>
          ) : undefined
        }
      />
    );
  }

  return (
    <div className="space-y-1.5">
      {filtered.map((ev: AuditEvidence) => (
        <div
          key={ev.id}
          className="flex items-center gap-3 rounded-lg border border-border bg-card p-3 hover:bg-accent/40 transition-colors"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded bg-muted flex-shrink-0">
            <FileText className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{ev.original_filename}</p>
            <p className="text-xs text-muted-foreground">{categoryLabel(ev.evidence_category)}</p>
          </div>
          <span className="hidden sm:inline-block text-xs text-muted-foreground flex-shrink-0">
            {formatDate(ev.created_at)}
          </span>
          <a
            href={evidenceDownloadUrl(ev.id)}
            className={cn(buttonVariants({ variant: "outline", size: "sm" }), "flex-shrink-0")}
          >
            <Download className="h-3.5 w-3.5 mr-1" />
            Download
          </a>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Frameworks tab
// ---------------------------------------------------------------------------

function FrameworkList({ search }: { search: string }) {
  const { data: frameworks, isLoading, isError, refetch } = useQuery({
    queryKey: ["regulatory-frameworks-library"],
    queryFn: () => listFrameworks({ include_global: true, active_only: false }),
  });

  const filtered = useMemo(() => {
    if (!frameworks) return [];
    const q = search.trim().toLowerCase();
    if (!q) return frameworks;
    return frameworks.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.code.toLowerCase().includes(q) ||
        (f.description ?? "").toLowerCase().includes(q)
    );
  }, [frameworks, search]);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border border-border">
            <div className="flex items-start gap-3">
              <Skeleton className="h-8 w-8 rounded flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-56" />
                <Skeleton className="h-3 w-80" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) return <ErrorState message="Failed to load regulatory frameworks." onRetry={refetch} />;

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={Shield}
        title={search ? "No frameworks match your search" : "No regulatory frameworks"}
        description="Regulatory frameworks are configured by QA Officers and System Administrators."
      />
    );
  }

  return (
    <div className="space-y-2">
      {filtered.map((fw: QualityFramework) => (
        <div
          key={fw.id}
          className="rounded-lg border border-border bg-card p-4 hover:bg-accent/40 transition-colors"
        >
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/10 flex-shrink-0 mt-0.5">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="text-sm font-semibold">{fw.name}</span>
                <span className="text-[10px] font-mono text-muted-foreground bg-muted border border-border rounded px-1.5 py-0.5">
                  {fw.code}
                </span>
                <SourceStatusBadge status={fw.source_status} />
                {fw.is_test_fixture && (
                  <span className="text-[10px] text-muted-foreground italic">[TEST FIXTURE]</span>
                )}
                {fw.is_mandatory && (
                  <span className="text-[10px] bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800 rounded px-1.5 py-0.5 font-medium">
                    Mandatory
                  </span>
                )}
              </div>
              {fw.description && (
                <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{fw.description}</p>
              )}
              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                <span>{fw.framework_type.replace(/_/g, " ")}</span>
                {fw.jurisdiction && <span>· {fw.jurisdiction}</span>}
                <span>· {fw.versions.length} version{fw.versions.length !== 1 ? "s" : ""}</span>
                {fw.institution_id === null && (
                  <span className="text-primary">· Global</span>
                )}
              </div>
            </div>
            <Link
              href={`/knowledge/foundation?framework=${fw.id}`}
              className={cn(
                buttonVariants({ variant: "ghost", size: "sm" }),
                "flex-shrink-0 text-xs"
              )}
            >
              <ExternalLink className="h-3.5 w-3.5 mr-1" />
              View
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function LibraryView() {
  const [tab, setTab] = useState<Tab>("evidence");
  const [search, setSearch] = useState("");
  const { isCoordinator } = useRole();

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "evidence", label: "Evidence Files", icon: <FileText className="h-4 w-4" /> },
    { id: "frameworks", label: "Regulatory Frameworks", icon: <BookOpen className="h-4 w-4" /> },
  ];

  return (
    <>
      <PageHeader
        title="Library"
        subtitle="Evidence files and regulatory framework documents"
        actions={
          isCoordinator ? (
            <Link href="/files/upload" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
              <Upload className="mr-1.5 h-4 w-4" />
              Upload Evidence
            </Link>
          ) : undefined
        }
      />

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border mb-5">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); setSearch(""); }}
            className={cn(
              "flex items-center gap-1.5 px-3 py-2 text-sm font-medium -mb-px border-b-2 transition-colors",
              tab === t.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          placeholder={tab === "evidence" ? "Search files…" : "Search frameworks…"}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Content */}
      {tab === "evidence" && <EvidenceList search={search} />}
      {tab === "frameworks" && <FrameworkList search={search} />}
    </>
  );
}
