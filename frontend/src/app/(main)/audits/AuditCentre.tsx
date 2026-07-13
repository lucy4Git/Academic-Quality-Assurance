"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Search, Filter, RotateCcw } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatDate } from "@/lib/utils";
import { useAuditRuns } from "@/hooks/useAuditRuns";
import { useModules } from "@/hooks/useModules";
import { useProgrammes } from "@/hooks/useProgrammes";
import {
  AGENT_TYPE_LABELS,
  AUDIT_RUN_STATUS_LABELS,
  AUDIT_RUN_STATUS_COLOURS,
  AUDIT_STATUS_LABELS,
  AUDIT_STATUS_COLOURS,
  type AuditRunBrief,
  type AuditRunStatus,
} from "@/types/auditRun";

function RunStatusBadge({ status }: { status: AuditRunStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", AUDIT_RUN_STATUS_COLOURS[status])}>
      {AUDIT_RUN_STATUS_LABELS[status]}
    </span>
  );
}

function ComplianceBar({ score }: { score: number | null }) {
  if (score === null) return <span className="text-xs text-muted-foreground w-28 text-right">—</span>;
  const colour = score >= 80 ? "bg-green-500" : score >= 60 ? "bg-amber-400" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", colour)} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
      <span className="text-xs tabular-nums w-9 text-right">{score.toFixed(0)}%</span>
    </div>
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
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-1.5 w-28" />
          <Skeleton className="h-3 w-20" />
        </div>
      ))}
    </div>
  );
}

function AuditRunRow({ run, moduleLabel, programmeLabel }: { run: AuditRunBrief; moduleLabel: string; programmeLabel: string }) {
  const router = useRouter();
  const scopeLabel = moduleLabel || programmeLabel || "—";
  const agentLabel = AGENT_TYPE_LABELS[run.agent_type] ?? run.agent_type;

  return (
    <div
      onClick={() => router.push(`/audits/${run.id}`)}
      className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors cursor-pointer group"
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        <ShieldCheck className="h-5 w-5 text-primary" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{agentLabel}</p>
        <p className="text-xs text-muted-foreground mt-0.5 truncate">{scopeLabel}</p>
      </div>

      <RunStatusBadge status={run.run_status} />

      {run.audit_status && (
        <span className={cn("hidden sm:inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", AUDIT_STATUS_COLOURS[run.audit_status])}>
          {AUDIT_STATUS_LABELS[run.audit_status]}
        </span>
      )}

      <ComplianceBar score={run.compliance_score} />

      <span className="text-xs text-muted-foreground hidden md:block w-20 text-right">
        {run.completed_at ? formatDate(run.completed_at) : formatDate(run.created_at)}
      </span>
    </div>
  );
}

export function AuditCentre() {
  const { data: runs, isLoading, isError, refetch } = useAuditRuns();
  const { data: modules } = useModules();
  const { data: programmes } = useProgrammes();

  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<AuditRunStatus | "">("");
  const [filterAgent, setFilterAgent] = useState<string>("");

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
    if (!runs) return [];
    let list = [...runs];
    if (filterStatus) list = list.filter((r) => r.run_status === filterStatus);
    if (filterAgent) list = list.filter((r) => r.agent_type === filterAgent);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter((r) => {
        const moduleLabel = r.module_id ? (moduleMap.get(r.module_id) ?? "") : "";
        const progLabel = r.programme_id ? (progMap.get(r.programme_id) ?? "") : "";
        const agentLabel = AGENT_TYPE_LABELS[r.agent_type] ?? r.agent_type;
        return moduleLabel.toLowerCase().includes(q) || progLabel.toLowerCase().includes(q) || agentLabel.toLowerCase().includes(q);
      });
    }
    return list;
  }, [runs, filterStatus, filterAgent, search, moduleMap, progMap]);

  const cls = "flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm";

  const total = runs?.length ?? 0;
  const completed = runs?.filter((r) => r.run_status === "completed").length ?? 0;

  return (
    <>
      <PageHeader
        title="Audit Centre"
        subtitle={runs ? `${completed} completed · ${total} total` : undefined}
        actions={
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Refresh
          </button>
        }
      />

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by agent, module, programme…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Filter className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value as AuditRunStatus | "")} className={cls}>
          <option value="">All statuses</option>
          {(["pending", "running", "completed", "failed"] as AuditRunStatus[]).map((s) => (
            <option key={s} value={s}>{AUDIT_RUN_STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)} className={cls}>
          <option value="">All agents</option>
          {Object.entries(AGENT_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {isLoading && <TableSkeleton />}
      {isError && <ErrorState message="Failed to load audit runs." onRetry={refetch} />}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={ShieldCheck}
          title={search || filterStatus || filterAgent ? "No runs match your filters" : "No audit runs yet"}
          description="Trigger an AI audit from any module or programme page to see results here."
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((run) => (
            <AuditRunRow
              key={run.id}
              run={run}
              moduleLabel={run.module_id ? (moduleMap.get(run.module_id) ?? run.module_id.slice(0, 8) + "…") : ""}
              programmeLabel={run.programme_id ? (progMap.get(run.programme_id) ?? run.programme_id.slice(0, 8) + "…") : ""}
            />
          ))}
        </div>
      )}
    </>
  );
}
