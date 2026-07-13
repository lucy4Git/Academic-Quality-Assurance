"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Play,
  RefreshCw,
  Shield,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { listModules } from "@/lib/api/modules";
import {
  triggerAccreditationReadiness,
  getLatestAccreditationReadiness,
  getAccreditationReadinessReport,
  type AccreditationReadinessReport,
  type SubAgentReadinessRead,
} from "@/lib/api/accreditationReadiness";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const RISK_COLOURS = {
  low: "text-green-700 bg-green-50 border-green-200",
  medium: "text-amber-700 bg-amber-50 border-amber-200",
  high: "text-red-700 bg-red-50 border-red-200",
  critical: "text-red-900 bg-red-100 border-red-300",
} as const;

const RISK_LABELS = {
  low: "Low Risk",
  medium: "Medium Risk",
  high: "High Risk",
  critical: "Critical Risk",
} as const;

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const r = size / 2 - 8;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const colour =
    score >= 80 ? "#16a34a" : score >= 60 ? "#d97706" : "#dc2626";
  return (
    <svg width={size} height={size} className="flex-shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth={8} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={colour}
        strokeWidth={8}
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x={size / 2}
        y={size / 2 + 5}
        textAnchor="middle"
        fontSize={size === 80 ? 16 : 13}
        fontWeight="700"
        fill={colour}
      >
        {Math.round(score)}
      </text>
    </svg>
  );
}

function SubAgentRow({ item }: { item: SubAgentReadinessRead }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-100 dark:border-slate-800 last:border-0">
      <div className="flex-shrink-0">
        {!item.has_run ? (
          <div className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700" />
        ) : item.passed ? (
          <CheckCircle2 className="w-5 h-5 text-green-500" />
        ) : (
          <XCircle className="w-5 h-5 text-red-500" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-800 dark:text-slate-100">
          {item.label}
        </div>
        <div className="text-xs text-slate-400">
          Weight: {item.weight}% · Threshold: {item.threshold}
        </div>
      </div>
      <div className="text-right flex-shrink-0">
        {item.has_run && item.overall_score != null ? (
          <span
            className={`text-sm font-semibold ${item.passed ? "text-green-600" : "text-red-600"}`}
          >
            {Math.round(item.overall_score)}
          </span>
        ) : (
          <span className="text-xs text-slate-400">Not run</span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report view
// ---------------------------------------------------------------------------

function ReportView({ report }: { report: AccreditationReadinessReport }) {
  const riskKey = report.risk_level as keyof typeof RISK_COLOURS;

  return (
    <div className="space-y-6">
      {/* Score summary */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {report.module_name}
            </h2>
            <div className="text-sm text-slate-500">
              {report.module_code} · {report.academic_year}
            </div>
          </div>
          <span
            className={`text-sm font-medium px-3 py-1 rounded-full border ${RISK_COLOURS[riskKey]}`}
          >
            {RISK_LABELS[riskKey]}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={report.overall_score} size={80} />
            <div className="text-xs text-slate-500 font-medium">Overall</div>
          </div>
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={report.presence_score} size={64} />
            <div className="text-xs text-slate-500">Checklist</div>
          </div>
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={report.quality_score} size={64} />
            <div className="text-xs text-slate-500">Quality</div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3">
            <div className="text-xs text-slate-500 mb-0.5">Evidence completeness</div>
            <div className="font-semibold text-slate-800 dark:text-slate-200">
              {Math.round(report.evidence_completeness_percentage)}%
            </div>
          </div>
          <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3">
            <div className="text-xs text-slate-500 mb-0.5">Unresolved findings</div>
            <div className="font-semibold text-slate-800 dark:text-slate-200">
              {report.findings_summary.unresolved} / {report.findings_summary.total}
            </div>
          </div>
        </div>
      </div>

      {/* Sub-agent checklist */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
          Compliance Checklist
        </h3>
        {report.sub_agent_readiness.map((item) => (
          <SubAgentRow key={item.group_id} item={item} />
        ))}
      </div>

      {/* Gaps */}
      {report.gaps.length > 0 && (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Accreditation Gaps ({report.gaps.length})
          </h3>
          <ul className="space-y-1.5">
            {report.gaps.map((gap, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
                <span className="text-red-400 mt-0.5 flex-shrink-0">·</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-blue-700 dark:text-blue-400 uppercase tracking-wide mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Recommendations
          </h3>
          <ul className="space-y-1.5">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-blue-800 dark:text-blue-300">
                <span className="mt-0.5 flex-shrink-0">{i + 1}.</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Summary */}
      {report.summary && (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-2">
            Summary
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-line">
            {report.summary}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Module run card
// ---------------------------------------------------------------------------

function ModuleRunCard({
  moduleId,
  moduleName,
  moduleCode,
}: {
  moduleId: string;
  moduleName: string;
  moduleCode: string;
}) {
  const qc = useQueryClient();
  const [showReport, setShowReport] = useState(false);

  const { data: latestRun, isLoading: runLoading } = useQuery({
    queryKey: ["accreditation-readiness-run", moduleId],
    queryFn: () => getLatestAccreditationReadiness(moduleId).catch(() => null),
    retry: false,
  });

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ["accreditation-readiness-report", latestRun?.id],
    queryFn: () => getAccreditationReadinessReport(latestRun!.id),
    enabled: showReport && latestRun?.run_status === "completed",
  });

  const trigger = useMutation({
    mutationFn: () => triggerAccreditationReadiness(moduleId),
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["accreditation-readiness-run", moduleId] });
      }, 3000);
    },
  });

  const status = latestRun?.run_status;
  const score = latestRun?.compliance_score;
  const auditStatus = latestRun?.audit_status;

  const scoreColour =
    score == null ? "text-slate-400"
    : score >= 80 ? "text-green-600"
    : score >= 60 ? "text-amber-600"
    : "text-red-600";

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
            {moduleName}
          </div>
          <div className="text-xs text-slate-500">{moduleCode}</div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {score != null && (
            <span className={`text-xl font-bold ${scoreColour}`}>
              {Math.round(score)}
            </span>
          )}
          <button
            onClick={() => trigger.mutate()}
            disabled={trigger.isPending || status === "running"}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-300 disabled:opacity-50 transition-colors"
          >
            {trigger.isPending || status === "running" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            {status === "running" ? "Running…" : "Run"}
          </button>
        </div>
      </div>

      {runLoading && (
        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <Loader2 className="w-3 h-3 animate-spin" />
          Loading…
        </div>
      )}

      {!runLoading && latestRun && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {status === "completed" && auditStatus && (
              <span className="text-xs px-1.5 py-0.5 rounded border capitalize font-medium
                text-slate-600 bg-slate-50 border-slate-200">
                {auditStatus.replace(/_/g, " ")}
              </span>
            )}
            {status === "running" && (
              <span className="text-xs text-blue-600 flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                Running
              </span>
            )}
            {status === "failed" && (
              <span className="text-xs text-red-500">Failed</span>
            )}
            <span className="text-xs text-slate-400">
              {new Date(latestRun.created_at).toLocaleDateString()}
            </span>
          </div>
          {status === "completed" && (
            <button
              onClick={() => setShowReport(!showReport)}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
            >
              {showReport ? "Hide report" : "View report"}
              <ChevronRight className={`w-3.5 h-3.5 transition-transform ${showReport ? "rotate-90" : ""}`} />
            </button>
          )}
        </div>
      )}

      {!runLoading && !latestRun && !trigger.isPending && (
        <p className="text-xs text-slate-400">No runs yet. Click Run to start.</p>
      )}

      {showReport && (
        <div className="mt-4 border-t border-slate-100 dark:border-slate-700 pt-4">
          {reportLoading && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading report…
            </div>
          )}
          {report && <ReportView report={report} />}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main workspace
// ---------------------------------------------------------------------------

export function AccreditationWorkspace() {
  const { data: modules, isLoading, isError, refetch } = useQuery({
    queryKey: ["modules-for-accreditation"],
    queryFn: () => listModules(),
  });

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="px-6 pt-6 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Accreditation Readiness
              </h1>
            </div>
            <p className="text-sm text-slate-500">
              Meta-audit aggregating 6 compliance agents — run per module to assess readiness
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {isLoading && (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            Loading modules…
          </div>
        )}
        {isError && (
          <div className="flex items-center justify-center py-16 text-red-500 text-sm">
            Failed to load modules.
          </div>
        )}
        {modules && modules.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Shield className="w-10 h-10 mb-3 text-slate-300" />
            <p className="text-sm">No modules available for your institution.</p>
          </div>
        )}
        {modules && modules.length > 0 && (
          <div className="grid gap-4 max-w-3xl">
            {modules.map((mod) => (
              <ModuleRunCard
                key={mod.id}
                moduleId={mod.id}
                moduleName={mod.name}
                moduleCode={mod.code}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
