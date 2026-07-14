"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Loader2,
  Shield,
  XCircle,
} from "lucide-react";
import { listAssessments } from "@/lib/api/regulatoryFramework";
import type {
  CriterionAssessmentResult,
  FrameworkAssessmentRunBrief,
} from "@/lib/api/regulatoryFramework";
import { useAuth } from "@/hooks/useAuth";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const RISK_COLOURS: Record<string, string> = {
  low: "text-green-700 bg-green-50 border-green-200",
  medium: "text-amber-700 bg-amber-50 border-amber-200",
  high: "text-red-700 bg-red-50 border-red-200",
  critical: "text-red-900 bg-red-100 border-red-300",
};

const READINESS_LABELS: Record<string, string> = {
  ready: "Ready",
  conditionally_ready: "Conditionally Ready",
  not_ready: "Not Ready",
};

function ScoreBar({ label, score, colour }: { label: string; score: number; colour: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">{label}</span>
        <span className={`text-xs font-semibold ${colour}`}>{Math.round(score)}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-700">
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width: `${Math.min(100, score)}%`,
            backgroundColor: score >= 85 ? "#16a34a" : score >= 70 ? "#d97706" : "#dc2626",
          }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Assessment row
// ---------------------------------------------------------------------------

function AssessmentRow({ run }: { run: FrameworkAssessmentRunBrief }) {
  const riskCls = run.risk_level ? RISK_COLOURS[run.risk_level] ?? "" : "";
  const hasMandatoryFail = (run.mandatory_failures ?? 0) > 0;

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800 space-y-3">
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
            hasMandatoryFail
              ? "bg-red-100 dark:bg-red-900/30"
              : "bg-green-100 dark:bg-green-900/30"
          }`}
        >
          {hasMandatoryFail ? (
            <XCircle className="w-4 h-4 text-red-600" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-green-600" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-slate-900 dark:text-slate-100 capitalize">
              {run.target_entity_type} assessment
            </span>
            {run.risk_level && (
              <span className={`text-xs px-2 py-0.5 rounded border font-medium ${riskCls}`}>
                {run.risk_level.charAt(0).toUpperCase() + run.risk_level.slice(1)} Risk
              </span>
            )}
            {run.readiness_status && (
              <span className="text-xs text-slate-500">
                {READINESS_LABELS[run.readiness_status] ?? run.readiness_status}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {new Date(run.created_at).toLocaleDateString()} ·{" "}
            {run.criteria_met ?? 0}/{run.criteria_total ?? 0} criteria met
            {hasMandatoryFail ? ` · ${run.mandatory_failures} mandatory failure(s)` : ""}
          </p>
        </div>
        {run.overall_score !== null && (
          <div className="flex-shrink-0 text-right">
            <div
              className={`text-xl font-bold ${
                run.overall_score >= 85
                  ? "text-green-600"
                  : run.overall_score >= 70
                  ? "text-amber-600"
                  : "text-red-600"
              }`}
            >
              {Math.round(run.overall_score)}%
            </div>
            <div className="text-xs text-slate-400">overall</div>
          </div>
        )}
      </div>

      {/* Score bars */}
      {run.mandatory_compliance_score !== null && (
        <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-700">
          <ScoreBar
            label="Mandatory Compliance"
            score={run.mandatory_compliance_score}
            colour={run.mandatory_compliance_score === 100 ? "text-green-600" : "text-red-600"}
          />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-400">
      <ClipboardList className="w-12 h-12 mb-3 opacity-30" />
      <p className="text-sm font-medium">No assessments yet</p>
      <p className="text-xs mt-1">
        Run a framework assessment from a module or programme to see readiness here.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function RegulatoryReadiness() {
  const { user } = useAuth();
  const institutionId = user?.institution_id ?? "";

  const { data: assessments = [], isLoading } = useQuery({
    queryKey: ["framework-assessments", institutionId],
    queryFn: () => listAssessments(institutionId),
    enabled: !!institutionId,
  });

  const totalAssessments = assessments.length;
  const mandatoryFails = assessments.filter((a) => (a.mandatory_failures ?? 0) > 0).length;
  const readyCount = assessments.filter((a) => a.readiness_status === "ready").length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Regulatory Readiness
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Framework assessment results across your institution
            </p>
          </div>
        </div>

        {/* Summary stats */}
        {totalAssessments > 0 && (
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div className="text-xl font-bold text-slate-900 dark:text-slate-100">
                {totalAssessments}
              </div>
              <div className="text-xs text-slate-500">Total assessments</div>
            </div>
            <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <div className="text-xl font-bold text-green-700 dark:text-green-400">
                {readyCount}
              </div>
              <div className="text-xs text-green-600 dark:text-green-500">Ready</div>
            </div>
            <div
              className={`p-3 rounded-lg border ${
                mandatoryFails > 0
                  ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                  : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700"
              }`}
            >
              <div
                className={`text-xl font-bold ${
                  mandatoryFails > 0 ? "text-red-700 dark:text-red-400" : "text-slate-400"
                }`}
              >
                {mandatoryFails}
              </div>
              <div
                className={`text-xs ${
                  mandatoryFails > 0 ? "text-red-600 dark:text-red-500" : "text-slate-400"
                }`}
              >
                Mandatory failures
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        ) : assessments.length === 0 ? (
          <EmptyState />
        ) : (
          assessments.map((run) => <AssessmentRow key={run.id} run={run} />)
        )}
      </div>
    </div>
  );
}
