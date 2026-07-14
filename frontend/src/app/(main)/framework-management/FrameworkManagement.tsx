"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Building2,
  CheckCircle2,
  ChevronRight,
  Globe,
  Layers,
  Loader2,
  Shield,
  XCircle,
} from "lucide-react";
import { listAuthorities, listFrameworks } from "@/lib/api/regulatoryFramework";
import type { QualityFramework, RegulatoryAuthority } from "@/lib/api/regulatoryFramework";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AUTHORITY_TYPE_LABELS: Record<string, string> = {
  national_regulator: "National Regulator",
  qualification_authority: "Qualification Authority",
  quality_council: "Quality Council",
  professional_council: "Professional Council",
  accreditation_body: "Accreditation Body",
  government_department: "Government Department",
  seta: "SETA",
  institution: "Institution",
  international_body: "International Body",
  custom: "Custom",
};

const FRAMEWORK_TYPE_LABELS: Record<string, string> = {
  quality_assurance: "Quality Assurance",
  accreditation: "Accreditation",
  programme_qualification: "Programme Qualification",
  professional_registration: "Professional Registration",
  nqf: "NQF",
  custom: "Custom",
};

const VERSION_STATUS_COLOURS: Record<string, string> = {
  active: "bg-green-100 text-green-800 border-green-200",
  draft: "bg-slate-100 text-slate-600 border-slate-200",
  under_review: "bg-amber-100 text-amber-800 border-amber-200",
  approved: "bg-blue-100 text-blue-800 border-blue-200",
  superseded: "bg-purple-100 text-purple-600 border-purple-200",
  retired: "bg-red-100 text-red-700 border-red-200",
  archived: "bg-slate-100 text-slate-400 border-slate-100",
};

function StatusBadge({ status }: { status: string }) {
  const cls = VERSION_STATUS_COLOURS[status] ?? "bg-slate-100 text-slate-500 border-slate-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Authority card
// ---------------------------------------------------------------------------

function AuthorityCard({ authority }: { authority: RegulatoryAuthority }) {
  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800 hover:border-blue-300 dark:hover:border-blue-600 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
          {authority.is_external ? (
            <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          ) : (
            <Building2 className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              {authority.short_name ?? authority.code}
            </span>
            <span className="text-xs text-slate-500 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded">
              {AUTHORITY_TYPE_LABELS[authority.authority_type] ?? authority.authority_type}
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 truncate">{authority.name}</p>
          {authority.jurisdiction && (
            <p className="text-xs text-slate-400 mt-0.5">{authority.jurisdiction} · {authority.country}</p>
          )}
        </div>
        {authority.is_active ? (
          <CheckCircle2 className="flex-shrink-0 w-4 h-4 text-green-500" />
        ) : (
          <XCircle className="flex-shrink-0 w-4 h-4 text-slate-400" />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Framework card
// ---------------------------------------------------------------------------

function FrameworkCard({
  framework,
  selected,
  onClick,
}: {
  framework: QualityFramework;
  selected: boolean;
  onClick: () => void;
}) {
  const activeVersions = framework.versions.filter((v) => v.status === "active");

  return (
    <button
      onClick={onClick}
      className={`w-full text-left border rounded-lg p-4 transition-all ${
        selected
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm"
          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-300 dark:hover:border-blue-600"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center ${
            selected ? "bg-blue-100 dark:bg-blue-800" : "bg-slate-100 dark:bg-slate-700"
          }`}
        >
          <BookOpen
            className={`w-5 h-5 ${selected ? "text-blue-600" : "text-slate-500"}`}
          />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              {framework.code}
            </span>
            {framework.is_mandatory && (
              <span className="text-xs px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded">
                Mandatory
              </span>
            )}
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 line-clamp-2">{framework.name}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="text-xs text-slate-400">
              {FRAMEWORK_TYPE_LABELS[framework.framework_type] ?? framework.framework_type}
            </span>
            {activeVersions.length > 0 && (
              <>
                <span className="text-slate-300 dark:text-slate-600">·</span>
                <StatusBadge status="active" />
                <span className="text-xs text-slate-500">{activeVersions[0].version_label ?? activeVersions[0].version_number}</span>
              </>
            )}
          </div>
        </div>
        <ChevronRight
          className={`flex-shrink-0 w-4 h-4 transition-colors ${
            selected ? "text-blue-500" : "text-slate-300"
          }`}
        />
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Framework detail panel
// ---------------------------------------------------------------------------

function FrameworkDetail({ framework }: { framework: QualityFramework }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {framework.name}
        </h3>
        {framework.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{framework.description}</p>
        )}
        <div className="flex gap-2 mt-3 flex-wrap">
          <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded">
            {FRAMEWORK_TYPE_LABELS[framework.framework_type] ?? framework.framework_type}
          </span>
          <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded">
            Scope: {framework.scope}
          </span>
          {framework.jurisdiction && (
            <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded">
              {framework.jurisdiction}
            </span>
          )}
        </div>
      </div>

      <div>
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Versions ({framework.versions.length})
        </h4>
        {framework.versions.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No versions defined yet.</p>
        ) : (
          <div className="space-y-2">
            {framework.versions.map((v) => (
              <div
                key={v.id}
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50"
              >
                <Layers className="w-4 h-4 flex-shrink-0 text-slate-400" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                      {v.version_label ?? v.version_number}
                    </span>
                    <StatusBadge status={v.status} />
                  </div>
                  {(v.effective_from || v.effective_to) && (
                    <p className="text-xs text-slate-400 mt-0.5">
                      {v.effective_from ? `From ${v.effective_from}` : ""}
                      {v.effective_from && v.effective_to ? " — " : ""}
                      {v.effective_to ? `To ${v.effective_to}` : ""}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function FrameworkManagement() {
  const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | null>(null);
  const [tab, setTab] = useState<"frameworks" | "authorities">("frameworks");

  const { data: frameworks = [], isLoading: fwLoading } = useQuery({
    queryKey: ["frameworks"],
    queryFn: () => listFrameworks({ include_global: true, active_only: false }),
  });

  const { data: authorities = [], isLoading: authLoading } = useQuery({
    queryKey: ["regulatory-authorities"],
    queryFn: () => listAuthorities({ include_global: true }),
  });

  const selectedFramework = frameworks.find((f) => f.id === selectedFrameworkId) ?? null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Framework Management
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Regulatory authorities and quality frameworks
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-4">
          {(["frameworks", "authorities"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm border border-slate-200 dark:border-slate-600"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              {t === "frameworks" ? `Frameworks (${frameworks.length})` : `Authorities (${authorities.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {tab === "frameworks" ? (
          <>
            {/* Left: framework list */}
            <div className="w-80 flex-shrink-0 border-r border-slate-200 dark:border-slate-700 overflow-y-auto">
              <div className="p-3 space-y-2">
                {fwLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                  </div>
                ) : frameworks.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 text-sm">
                    No frameworks found.
                    <br />
                    <span className="text-xs">Run the seed script to load test fixtures.</span>
                  </div>
                ) : (
                  frameworks.map((fw) => (
                    <FrameworkCard
                      key={fw.id}
                      framework={fw}
                      selected={fw.id === selectedFrameworkId}
                      onClick={() =>
                        setSelectedFrameworkId(fw.id === selectedFrameworkId ? null : fw.id)
                      }
                    />
                  ))
                )}
              </div>
            </div>

            {/* Right: detail */}
            <div className="flex-1 overflow-y-auto p-6">
              {selectedFramework ? (
                <FrameworkDetail framework={selectedFramework} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-400">
                  <BookOpen className="w-12 h-12 mb-3 opacity-30" />
                  <p className="text-sm">Select a framework to view details</p>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Authorities tab */
          <div className="flex-1 overflow-y-auto p-4">
            {authLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
              </div>
            ) : authorities.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-sm">
                No regulatory authorities found.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {authorities.map((auth) => (
                  <AuthorityCard key={auth.id} authority={auth} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
