"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  SearchCheck,
  Plus,
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  Filter,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, formatDate } from "@/lib/utils";
import { useAudits, useDeleteAudit } from "@/hooks/useModuleAudits";
import { useModules } from "@/hooks/useModules";
import { useProgrammes } from "@/hooks/useProgrammes";
import { useRole } from "@/hooks/useRole";
import {
  MODULE_AUDIT_STATUS_LABELS,
  MODULE_AUDIT_STATUS_COLOURS,
  type ModuleAudit,
  type ModuleAuditBrief,
  type ModuleAuditStatus,
} from "@/types";

function ComplianceBar({ pct }: { pct: number }) {
  const colour =
    pct >= 90 ? "bg-green-500" : pct >= 70 ? "bg-amber-400" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", colour)}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-xs tabular-nums w-9 text-right">{pct.toFixed(0)}%</span>
    </div>
  );
}

function StatusBadge({ status }: { status: ModuleAuditStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        MODULE_AUDIT_STATUS_COLOURS[status]
      )}
    >
      {MODULE_AUDIT_STATUS_LABELS[status]}
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
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-1.5 w-28" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function AuditCentre() {
  const router = useRouter();
  const { isCoordinator, isSysAdmin, isQAOfficer } = useRole();
  const { data: audits, isLoading, isError, refetch } = useAudits();
  const { data: modules } = useModules();
  const { data: programmes } = useProgrammes();
  const deleteMutation = useDeleteAudit();

  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<ModuleAuditStatus | "">("");
  const [filterProg, setFilterProg] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<ModuleAuditBrief | null>(null);

  const moduleMap = useMemo(() => {
    const m = new Map<string, string>();
    modules?.forEach((mod) => m.set(mod.id, `${mod.code} — ${mod.name}`));
    return m;
  }, [modules]);

  const progMap = useMemo(() => {
    const m = new Map<string, string>();
    programmes?.forEach((p) => m.set(p.id, `${p.name} (${p.code})`));
    return m;
  }, [programmes]);

  const filtered = useMemo(() => {
    if (!audits) return [];
    let list = [...audits];
    if (filterStatus) list = list.filter((a) => a.status === filterStatus);
    if (filterProg) list = list.filter((a) => a.programme_id === filterProg);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (a) =>
          (moduleMap.get(a.module_id) ?? "").toLowerCase().includes(q) ||
          a.academic_year.includes(q) ||
          (progMap.get(a.programme_id) ?? "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [audits, search, filterStatus, filterProg, moduleMap, progMap]);

  const canCreate = isCoordinator;
  const canDelete = isSysAdmin || isQAOfficer;

  const cls = "flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm";

  return (
    <>
      <PageHeader
        title="Audit Centre"
        subtitle={audits ? `${audits.length} audit${audits.length !== 1 ? "s" : ""}` : undefined}
        actions={
          canCreate ? (
            <Link href="/audits/new" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
              <Plus className="mr-1.5 h-4 w-4" />
              New Audit
            </Link>
          ) : undefined
        }
      />

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by module, programme, year…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Filter className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as ModuleAuditStatus | "")}
          className={cls}
        >
          <option value="">All statuses</option>
          {(["draft", "compliant", "at_risk", "non_compliant"] as ModuleAuditStatus[]).map((s) => (
            <option key={s} value={s}>{MODULE_AUDIT_STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select
          value={filterProg}
          onChange={(e) => setFilterProg(e.target.value)}
          className={cls}
        >
          <option value="">All programmes</option>
          {programmes?.map((p) => (
            <option key={p.id} value={p.id}>{p.code} — {p.name}</option>
          ))}
        </select>
      </div>

      {isLoading && <TableSkeleton />}
      {isError && <ErrorState message="Failed to load audits." onRetry={refetch} />}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={SearchCheck}
          title={search || filterStatus || filterProg ? "No audits match your filters" : "No audits yet"}
          description={canCreate ? "Create your first module folder audit to begin." : "No module folder audits have been created yet."}
          action={
            canCreate && !search ? (
              <Link href="/audits/new" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
                <Plus className="mr-1.5 h-4 w-4" />
                New Audit
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((audit) => (
            <div
              key={audit.id}
              className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <SearchCheck className="h-5 w-5 text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <button
                  onClick={() => router.push(`/audits/${audit.id}`)}
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
                >
                  {moduleMap.get(audit.module_id) ?? audit.module_id.slice(0, 8) + "…"}
                </button>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {progMap.get(audit.programme_id) ?? "—"} · {audit.academic_year}
                </p>
              </div>

              <StatusBadge status={audit.status} />
              <ComplianceBar pct={audit.compliance_percentage} />

              <span className="text-xs text-muted-foreground hidden md:block w-20 text-right">
                {formatDate(audit.updated_at)}
              </span>

              <DropdownMenu>
                <DropdownMenuTrigger
                  className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  aria-label="Audit actions"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                  <DropdownMenuItem onClick={() => router.push(`/audits/${audit.id}`)}>
                    <Eye className="mr-2 h-4 w-4" /> View Audit
                  </DropdownMenuItem>
                  {canDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setDeleteTarget(audit)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Audit"
        description={`Are you sure you want to delete this audit? This action cannot be undone.`}
        confirmLabel="Delete Audit"
        isPending={deleteMutation.isPending}
        onConfirm={async () => {
          if (deleteTarget) await deleteMutation.mutateAsync(deleteTarget.id);
          setDeleteTarget(null);
        }}
      />
    </>
  );
}
