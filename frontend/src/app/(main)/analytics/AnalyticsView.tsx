"use client";

import { useDashboard, useComplianceSummary } from "@/hooks/useReporting";
import type { InstitutionStats, KnowledgeIndexEntry } from "@/types/reporting";

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: number | string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

function KnowledgeIndexBadge({ entry }: { entry: KnowledgeIndexEntry }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3">
      <div>
        <p className="text-sm font-medium text-gray-900">
          {entry.institution_code} — {entry.ikp_version}
        </p>
        <p className="text-xs text-gray-400">{entry.collection}</p>
      </div>
      <div className="flex items-center gap-2">
        {entry.chunk_count !== null && (
          <span className="text-xs text-gray-500">{entry.chunk_count} chunks</span>
        )}
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            entry.indexed
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {entry.indexed ? "Indexed" : "Not indexed"}
        </span>
      </div>
    </div>
  );
}

function InstitutionCard({ inst }: { inst: InstitutionStats }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-gray-900">{inst.institution_name}</p>
          <p className="text-xs text-gray-400">
            {inst.institution_code} · {inst.institution_type}
          </p>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            inst.knowledge_indexed
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {inst.knowledge_indexed ? "Qdrant ✓" : "Not indexed"}
        </span>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.faculty_count}</p>
          <p className="text-xs text-gray-400">Faculties</p>
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.programme_count}</p>
          <p className="text-xs text-gray-400">Programmes</p>
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.module_count}</p>
          <p className="text-xs text-gray-400">Modules</p>
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.audit_run_count}</p>
          <p className="text-xs text-gray-400">Audit runs</p>
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.evidence_file_count}</p>
          <p className="text-xs text-gray-400">Files</p>
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{inst.department_count}</p>
          <p className="text-xs text-gray-400">Departments</p>
        </div>
      </div>
    </div>
  );
}

export function AnalyticsView() {
  const { data: dashboard, isLoading, error } = useDashboard();
  const { data: compliance } = useComplianceSummary();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400">
        Loading analytics…
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        Failed to load analytics data.
      </div>
    );
  }

  const auditRate =
    dashboard.audit_run_count > 0
      ? Math.round((dashboard.completed_audit_count / dashboard.audit_run_count) * 100)
      : 0;

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {dashboard.is_admin_view
            ? "Platform-wide aggregate view"
            : "Institutional quality metrics"}
          {" · "}Generated {new Date(dashboard.generated_at).toLocaleString()}
        </p>
      </div>

      {/* Platform summary */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
          Platform summary
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Institutions" value={dashboard.institution_count} />
          <StatCard label="Programmes" value={dashboard.programme_count} />
          <StatCard label="Modules" value={dashboard.module_count} />
          <StatCard label="Evidence files" value={dashboard.evidence_file_count} />
          <StatCard
            label="Audit runs"
            value={dashboard.audit_run_count}
            sub={`${dashboard.completed_audit_count} completed · ${dashboard.failed_audit_count} failed`}
          />
          <StatCard label="Faculties" value={dashboard.faculty_count} />
          <StatCard label="Departments" value={dashboard.department_count} />
          <StatCard label="Completion rate" value={`${auditRate}%`} sub="audit runs" />
        </div>
      </div>

      {/* Compliance summary */}
      {compliance && (
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Compliance overview — {compliance.institution_code}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard label="Total modules" value={compliance.total_modules} />
            <StatCard
              label="Compliance rate"
              value={`${compliance.compliance_rate_pct}%`}
              sub={`${compliance.audited_modules} modules audited`}
            />
            <StatCard label="Unaudited" value={compliance.unaudited_count} />
            <StatCard label="At risk" value={compliance.at_risk_count} />
          </div>
        </div>
      )}

      {/* Knowledge index status */}
      {dashboard.knowledge_index_status.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Knowledge index status
          </h2>
          <div className="space-y-2">
            {dashboard.knowledge_index_status.map((entry, i) => (
              <KnowledgeIndexBadge key={i} entry={entry} />
            ))}
          </div>
        </div>
      )}

      {/* Per-institution breakdown */}
      {dashboard.by_institution.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Per-institution breakdown
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {dashboard.by_institution.map((inst) => (
              <InstitutionCard key={inst.institution_id} inst={inst} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
