"use client";

import Link from "next/link";
import { ShieldCheck, ArrowLeft, Clock, CheckCircle2, XCircle, AlertTriangle, Info } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import { cn, formatDateTime } from "@/lib/utils";
import { useAuditRun } from "@/hooks/useAuditRuns";
import { useModule } from "@/hooks/useModules";
import {
  AGENT_TYPE_LABELS,
  AUDIT_RUN_STATUS_LABELS,
  AUDIT_RUN_STATUS_COLOURS,
  AUDIT_STATUS_LABELS,
  AUDIT_STATUS_COLOURS,
  FINDING_SEVERITY_COLOURS,
  type AuditFindingRead,
  type AuditRunStatus,
  type AuditStatus,
  type FindingSeverity,
} from "@/types/auditRun";

function RunStatusBadge({ status }: { status: AuditRunStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold", AUDIT_RUN_STATUS_COLOURS[status])}>
      {AUDIT_RUN_STATUS_LABELS[status]}
    </span>
  );
}

function AuditStatusBadge({ status }: { status: AuditStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold", AUDIT_STATUS_COLOURS[status])}>
      {AUDIT_STATUS_LABELS[status]}
    </span>
  );
}

function SeverityIcon({ severity }: { severity: FindingSeverity }) {
  if (severity === "critical" || severity === "high") return <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />;
  if (severity === "medium") return <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />;
  if (severity === "low") return <CheckCircle2 className="h-4 w-4 text-blue-500 flex-shrink-0" />;
  return <Info className="h-4 w-4 text-slate-400 flex-shrink-0" />;
}

function FindingCard({ finding }: { finding: AuditFindingRead }) {
  return (
    <div className="flex gap-3 p-4 rounded-lg border border-border bg-card">
      <SeverityIcon severity={finding.severity} />
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-foreground">{finding.title}</p>
          <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold", FINDING_SEVERITY_COLOURS[finding.severity])}>
            {finding.severity}
          </span>
          {finding.is_resolved && (
            <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold text-green-700 bg-green-50 border-green-200">
              Resolved
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{finding.description}</p>
        {finding.recommendation && (
          <p className="text-xs text-foreground/70 italic">Recommendation: {finding.recommendation}</p>
        )}
      </div>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between"><Skeleton className="h-8 w-56" /><Skeleton className="h-8 w-20" /></div>
      <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

export function AuditDetailView({ id }: { id: string }) {
  const { data: run, isLoading, isError, refetch } = useAuditRun(id);
  const { data: module } = useModule(run?.module_id ?? "");

  if (isLoading) return <DetailSkeleton />;
  if (isError || !run) return <ErrorState title="Audit run not found" onRetry={() => refetch()} />;

  const agentLabel = AGENT_TYPE_LABELS[run.agent_type] ?? run.agent_type;
  const scopeLabel = module ? `${module.code} — ${module.name}` : run.module_id ? run.module_id.slice(0, 8) + "…" : "Programme-scoped";

  const criticalCount = run.findings.filter((f) => f.severity === "critical").length;
  const highCount = run.findings.filter((f) => f.severity === "high").length;
  const mediumCount = run.findings.filter((f) => f.severity === "medium").length;
  const lowCount = run.findings.filter((f) => f.severity === "low").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={agentLabel}
        subtitle={scopeLabel}
        actions={
          <Link href="/audits" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Audit Centre
          </Link>
        }
      />

      {/* Status + compliance summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Run Status</p>
            <RunStatusBadge status={run.run_status} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Audit Status</p>
            {run.audit_status ? <AuditStatusBadge status={run.audit_status} /> : <p className="text-sm text-muted-foreground">—</p>}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Compliance Score</p>
            {run.compliance_score !== null ? (
              <p className={cn("text-2xl font-bold tabular-nums", run.compliance_score >= 80 ? "text-green-600" : run.compliance_score >= 60 ? "text-amber-600" : "text-red-600")}>
                {run.compliance_score.toFixed(0)}%
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">—</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Findings</p>
            <div className="flex items-center gap-1.5 flex-wrap">
              {criticalCount > 0 && <span className="text-xs font-semibold text-red-700">{criticalCount} critical</span>}
              {highCount > 0 && <span className="text-xs font-semibold text-red-500">{highCount} high</span>}
              {mediumCount > 0 && <span className="text-xs font-semibold text-amber-600">{mediumCount} med</span>}
              {lowCount > 0 && <span className="text-xs font-semibold text-blue-600">{lowCount} low</span>}
              {run.findings.length === 0 && <span className="text-sm text-muted-foreground">None</span>}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Documents */}
      {(run.documents_present !== null || run.documents_missing !== null) && (
        <div className="grid grid-cols-2 gap-3">
          <Card>
            <CardContent className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground">Documents Present</p>
              <p className="text-2xl font-bold text-green-600">{run.documents_present ?? 0}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground">Documents Missing</p>
              <p className="text-2xl font-bold text-red-600">{run.documents_missing ?? 0}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Summary */}
      {run.summary && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" /> AI Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{run.summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Findings */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Findings
            <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">{run.findings.length}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {run.findings.length === 0 ? (
            <p className="text-sm text-muted-foreground">No findings recorded for this audit run.</p>
          ) : (
            <div className="space-y-2">
              {run.findings.map((f) => <FindingCard key={f.id} finding={f} />)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Clock className="h-4 w-4" /> Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-xs text-muted-foreground">
            <div className="flex justify-between">
              <span>Created</span>
              <span>{formatDateTime(run.created_at)}</span>
            </div>
            {run.started_at && (
              <div className="flex justify-between">
                <span>Started</span>
                <span>{formatDateTime(run.started_at)}</span>
              </div>
            )}
            {run.completed_at && (
              <div className="flex justify-between">
                <span>Completed</span>
                <span>{formatDateTime(run.completed_at)}</span>
              </div>
            )}
          </div>
          {run.error_message && (
            <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
              <span className="font-semibold">Error: </span>{run.error_message}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
