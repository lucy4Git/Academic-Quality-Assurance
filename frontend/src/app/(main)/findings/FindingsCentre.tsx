"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  FileSearch,
  Filter,
  Loader2,
  RefreshCw,
  TrendingUp,
  XCircle,
} from "lucide-react";
import {
  FINDING_SEVERITY_COLOURS,
  FINDING_STATUS_COLOURS,
  FINDING_STATUS_LABELS,
  type AuditFindingRead,
} from "@/types/auditRun";
import type { FindingSeverity, FindingStatus, FindingType } from "@/types/enums";
import { useFindings, useFindingHistory, useFindingTransition } from "@/hooks/useFindings";
import { useRole } from "@/hooks/useRole";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SEVERITY_LABELS: Record<FindingSeverity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  info: "Info",
};

const TYPE_LABELS: Record<FindingType, string> = {
  missing_document: "Missing Document",
  misclassified: "Misclassified",
  quality_issue: "Quality Issue",
  recommendation: "Recommendation",
  info: "Info",
};

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "acknowledged", label: "Acknowledged" },
  { value: "assigned", label: "Assigned" },
  { value: "in_progress", label: "In Progress" },
  { value: "resolution_submitted", label: "Resolution Submitted" },
  { value: "under_review", label: "Under Review" },
  { value: "resolved", label: "Resolved" },
  { value: "rejected", label: "Rejected" },
  { value: "reopened", label: "Reopened" },
  { value: "deferred", label: "Deferred" },
  { value: "escalated", label: "Escalated" },
  { value: "closed", label: "Closed" },
];

const SEVERITY_OPTIONS = [
  { value: "", label: "All severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
  { value: "info", label: "Info" },
];

// ---------------------------------------------------------------------------
// Severity icon
// ---------------------------------------------------------------------------

function SeverityIcon({ severity }: { severity: FindingSeverity }) {
  if (severity === "critical" || severity === "high")
    return <XCircle className="w-4 h-4 text-red-600" />;
  if (severity === "medium")
    return <AlertTriangle className="w-4 h-4 text-amber-500" />;
  if (severity === "low")
    return <TrendingUp className="w-4 h-4 text-blue-500" />;
  return <FileSearch className="w-4 h-4 text-slate-400" />;
}

// ---------------------------------------------------------------------------
// Finding detail panel
// ---------------------------------------------------------------------------

function FindingDetail({
  finding,
  onClose,
}: {
  finding: AuditFindingRead;
  onClose: () => void;
}) {
  const { data: history, isLoading: histLoading } = useFindingHistory(finding.id);
  const transition = useFindingTransition();
  const [transNote, setTransNote] = useState("");
  const { isQAOfficer, isCoordinator } = useRole();

  const handleTransition = (action: string) => {
    transition.mutate(
      { id: finding.id, action, note: transNote || undefined },
      { onSuccess: () => setTransNote("") },
    );
  };

  const canAcknowledge = finding.status === "open" && isCoordinator;
  const canStart = ["acknowledged", "assigned", "reopened"].includes(finding.status);
  const canSubmit = finding.status === "in_progress";
  const canReview = finding.status === "resolution_submitted" && isQAOfficer;
  const canApprove = finding.status === "under_review" && isQAOfficer;
  const canReject = finding.status === "under_review" && isQAOfficer;
  const canReopen = finding.status === "resolved" && isQAOfficer;
  const canClose = ["open", "resolved"].includes(finding.status) && isQAOfficer;
  const canEscalate =
    !["resolved", "closed", "escalated"].includes(finding.status) && isCoordinator;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
      />
      <div className="relative w-full max-w-xl h-full bg-white dark:bg-slate-900 shadow-2xl overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <SeverityIcon severity={finding.severity} />
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full border ${FINDING_SEVERITY_COLOURS[finding.severity]}`}
              >
                {SEVERITY_LABELS[finding.severity]}
              </span>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full border ${FINDING_STATUS_COLOURS[finding.status as FindingStatus]}`}
              >
                {FINDING_STATUS_LABELS[finding.status as FindingStatus] ?? finding.status}
              </span>
            </div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 leading-tight">
              {finding.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex-shrink-0 mt-0.5"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 px-6 py-4 space-y-5">
          {/* Meta */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-slate-500 mb-0.5">Type</div>
              <div className="font-medium text-slate-800 dark:text-slate-200">
                {TYPE_LABELS[finding.finding_type]}
              </div>
            </div>
            {finding.document_category && (
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Category</div>
                <div className="font-medium text-slate-800 dark:text-slate-200 capitalize">
                  {finding.document_category.replace(/_/g, " ")}
                </div>
              </div>
            )}
            {finding.due_date && (
              <div>
                <div className="text-xs text-slate-500 mb-0.5">Due</div>
                <div className="font-medium text-slate-800 dark:text-slate-200 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-500" />
                  {finding.due_date}
                </div>
              </div>
            )}
            <div>
              <div className="text-xs text-slate-500 mb-0.5">Raised</div>
              <div className="text-slate-700 dark:text-slate-300">
                {new Date(finding.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Description
            </h3>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {finding.description}
            </p>
          </div>

          {/* Recommendation */}
          <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg p-4 border border-blue-100 dark:border-blue-900">
            <h3 className="text-xs font-semibold text-blue-700 dark:text-blue-400 uppercase tracking-wide mb-1.5">
              Recommendation
            </h3>
            <p className="text-sm text-blue-800 dark:text-blue-300 leading-relaxed">
              {finding.recommendation}
            </p>
          </div>

          {/* Resolution note */}
          {finding.resolved_note && (
            <div className="bg-green-50 dark:bg-green-950/30 rounded-lg p-4 border border-green-100 dark:border-green-900">
              <h3 className="text-xs font-semibold text-green-700 dark:text-green-400 uppercase tracking-wide mb-1.5">
                Resolution Note
              </h3>
              <p className="text-sm text-green-800 dark:text-green-300">
                {finding.resolved_note}
              </p>
            </div>
          )}

          {/* Actions */}
          {(canAcknowledge || canStart || canSubmit || canReview || canApprove ||
            canReject || canReopen || canClose || canEscalate) && (
            <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Actions
              </h3>
              <textarea
                value={transNote}
                onChange={(e) => setTransNote(e.target.value)}
                placeholder="Add a note (optional)..."
                className="w-full text-sm rounded-md border border-slate-300 dark:border-slate-600 bg-transparent px-3 py-2 text-slate-800 dark:text-slate-200 placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
              />
              <div className="flex flex-wrap gap-2">
                {canAcknowledge && (
                  <ActionButton
                    label="Acknowledge"
                    colour="blue"
                    loading={transition.isPending}
                    onClick={() => handleTransition("acknowledge")}
                  />
                )}
                {canStart && (
                  <ActionButton
                    label="Start Progress"
                    colour="indigo"
                    loading={transition.isPending}
                    onClick={() => handleTransition("start")}
                  />
                )}
                {canSubmit && (
                  <ActionButton
                    label="Submit Resolution"
                    colour="violet"
                    loading={transition.isPending}
                    onClick={() => handleTransition("submit-resolution")}
                  />
                )}
                {canReview && (
                  <ActionButton
                    label="Mark Under Review"
                    colour="amber"
                    loading={transition.isPending}
                    onClick={() => handleTransition("request-review")}
                  />
                )}
                {canApprove && (
                  <ActionButton
                    label="Approve"
                    colour="green"
                    loading={transition.isPending}
                    onClick={() => handleTransition("approve")}
                  />
                )}
                {canReject && (
                  <ActionButton
                    label="Reject"
                    colour="red"
                    loading={transition.isPending}
                    onClick={() => handleTransition("reject")}
                  />
                )}
                {canReopen && (
                  <ActionButton
                    label="Reopen"
                    colour="orange"
                    loading={transition.isPending}
                    onClick={() => handleTransition("reopen")}
                  />
                )}
                {canClose && (
                  <ActionButton
                    label="Close"
                    colour="slate"
                    loading={transition.isPending}
                    onClick={() => handleTransition("close")}
                  />
                )}
                {canEscalate && (
                  <ActionButton
                    label="Escalate"
                    colour="rose"
                    loading={transition.isPending}
                    onClick={() => handleTransition("escalate")}
                  />
                )}
              </div>
              {transition.isError && (
                <p className="text-xs text-red-600">
                  {String(transition.error)}
                </p>
              )}
            </div>
          )}

          {/* History */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Audit Trail
            </h3>
            {histLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
            ) : history && history.length > 0 ? (
              <ol className="space-y-2">
                {history.map((h) => (
                  <li key={h.id} className="flex items-start gap-2 text-sm">
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                    <div>
                      <span className="font-medium text-slate-700 dark:text-slate-300">
                        {h.from_status ? `${h.from_status} → ` : ""}
                        {h.to_status}
                      </span>
                      {h.note && (
                        <span className="text-slate-500"> · {h.note}</span>
                      )}
                      <div className="text-xs text-slate-400">
                        {new Date(h.created_at).toLocaleString()}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-slate-400">No transitions recorded yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ActionButton({
  label,
  colour,
  loading,
  onClick,
}: {
  label: string;
  colour: string;
  loading: boolean;
  onClick: () => void;
}) {
  const colours: Record<string, string> = {
    blue: "bg-blue-600 hover:bg-blue-700 text-white",
    indigo: "bg-indigo-600 hover:bg-indigo-700 text-white",
    violet: "bg-violet-600 hover:bg-violet-700 text-white",
    amber: "bg-amber-500 hover:bg-amber-600 text-white",
    green: "bg-green-600 hover:bg-green-700 text-white",
    red: "bg-red-600 hover:bg-red-700 text-white",
    orange: "bg-orange-500 hover:bg-orange-600 text-white",
    rose: "bg-rose-600 hover:bg-rose-700 text-white",
    slate: "bg-slate-500 hover:bg-slate-600 text-white",
  };
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`text-xs font-medium px-3 py-1.5 rounded-md transition-colors disabled:opacity-50 ${colours[colour] ?? colours.blue}`}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin inline" /> : label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Finding row
// ---------------------------------------------------------------------------

function FindingRow({
  finding,
  onClick,
}: {
  finding: AuditFindingRead;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left border-b border-slate-100 dark:border-slate-800 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex items-start gap-3"
    >
      <div className="mt-0.5">
        <SeverityIcon severity={finding.severity} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">
            {finding.title}
          </span>
          <span
            className={`text-xs px-1.5 py-0.5 rounded border font-medium flex-shrink-0 ${FINDING_SEVERITY_COLOURS[finding.severity]}`}
          >
            {SEVERITY_LABELS[finding.severity]}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span
            className={`px-1.5 py-0.5 rounded border font-medium ${FINDING_STATUS_COLOURS[finding.status as FindingStatus]}`}
          >
            {FINDING_STATUS_LABELS[finding.status as FindingStatus] ?? finding.status}
          </span>
          <span>{TYPE_LABELS[finding.finding_type]}</span>
          {finding.due_date && (
            <span className="flex items-center gap-0.5 text-amber-600">
              <Clock className="w-3 h-3" />
              {finding.due_date}
            </span>
          )}
          <span className="ml-auto">{new Date(finding.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0 mt-0.5" />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function FindingsCentre() {
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: findings, isLoading, isError, refetch } = useFindings({
    status: statusFilter || undefined,
    severity: severityFilter || undefined,
    limit: 100,
  });

  const selectedFinding = findings?.find((f) => f.id === selectedId) ?? null;

  // Summary counts
  const counts = {
    total: findings?.length ?? 0,
    open: findings?.filter((f) => f.status === "open").length ?? 0,
    critical: findings?.filter((f) => f.severity === "critical").length ?? 0,
    resolved: findings?.filter((f) => f.status === "resolved" || f.status === "closed").length ?? 0,
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Header */}
      <div className="px-6 pt-6 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              Findings
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Audit findings lifecycle — review, resolve, and track corrective actions
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[
            { label: "Total", value: counts.total, colour: "text-slate-700" },
            { label: "Open", value: counts.open, colour: "text-amber-600" },
            { label: "Critical", value: counts.critical, colour: "text-red-600" },
            { label: "Resolved", value: counts.resolved, colour: "text-green-600" },
          ].map((c) => (
            <div
              key={c.label}
              className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3"
            >
              <div className={`text-2xl font-semibold ${c.colour}`}>{c.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{c.label}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {SEVERITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          {(statusFilter || severityFilter) && (
            <button
              onClick={() => { setStatusFilter(""); setSeverityFilter(""); }}
              className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            Loading findings…
          </div>
        )}
        {isError && (
          <div className="flex items-center justify-center py-16 text-red-500 text-sm">
            Failed to load findings.
          </div>
        )}
        {!isLoading && !isError && (!findings || findings.length === 0) && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <CheckCircle2 className="w-10 h-10 mb-3 text-green-400" />
            <p className="text-sm font-medium">No findings match your filters</p>
            <p className="text-xs mt-1">Try adjusting the status or severity filter</p>
          </div>
        )}
        {findings && findings.length > 0 && (
          <div>
            {findings.map((f) => (
              <FindingRow
                key={f.id}
                finding={f}
                onClick={() => setSelectedId(f.id === selectedId ? null : f.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selectedFinding && (
        <FindingDetail
          finding={selectedFinding}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
