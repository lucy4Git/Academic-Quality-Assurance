"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle, XCircle, GitMerge, RefreshCw } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useInstitutions } from "@/hooks/useInstitutions";
import {
  useApproveCandidate,
  useExtractionCandidates,
  useExtractionRuns,
  useExtractionStatistics,
  useRejectCandidate,
  useReviewQueue,
  useTriggerExtraction,
} from "@/hooks/useExtraction";
import { useAcquisitionDownloads } from "@/hooks/useAcquisition";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ExtractionCandidate } from "@/lib/api/extraction";

// ---- Badge helpers ---------------------------------------------------------

const MAPPING_STYLES: Record<string, string> = {
  auto_mapped: "bg-green-700",
  needs_review: "bg-amber-500",
  approved: "bg-green-600",
  rejected: "bg-red-600",
};

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-600",
  needs_review: "bg-amber-500",
  failed: "bg-red-600",
  running: "bg-blue-600",
  pending: "bg-muted text-foreground",
};

const QUALITY_STYLES: Record<string, string> = {
  good: "bg-green-600",
  partial: "bg-amber-500",
  poor: "bg-red-600",
};

function MappingBadge({ status }: { status: string }) {
  return (
    <Badge className={MAPPING_STYLES[status] ?? "bg-muted text-foreground"}>
      {status.replace("_", " ")}
    </Badge>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <Badge className={STATUS_STYLES[status] ?? "bg-muted text-foreground"}>
      {status.replace("_", " ")}
    </Badge>
  );
}

function EntityTypeBadge({ type }: { type: string }) {
  return (
    <Badge variant="outline" className="font-mono text-xs">
      {type.replace("_", " ")}
    </Badge>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const cls = pct >= 80 ? "bg-green-600" : pct >= 60 ? "bg-amber-500" : "bg-muted text-foreground";
  return <Badge className={cls}>{pct}%</Badge>;
}

function fmt(v: string | null) {
  if (!v) return "—";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString();
}

// ---- Stat card -------------------------------------------------------------

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ---- Review action buttons -------------------------------------------------

function ReviewActions({ candidate }: { candidate: ExtractionCandidate }) {
  const approve = useApproveCandidate();
  const reject = useRejectCandidate();
  const isPending = approve.isPending || reject.isPending;

  if (candidate.mapping_status === "approved") {
    return <span className="text-green-600 text-xs font-medium">Approved</span>;
  }
  if (candidate.mapping_status === "rejected") {
    return <span className="text-red-500 text-xs font-medium">Rejected</span>;
  }

  return (
    <div className="flex gap-1">
      <button
        disabled={isPending}
        onClick={() => approve.mutate({ candidateId: candidate.id, payload: {} })}
        className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium bg-green-700 text-white hover:bg-green-800 disabled:opacity-50"
      >
        <CheckCircle className="h-3 w-3" /> Approve
      </button>
      <button
        disabled={isPending}
        onClick={() => reject.mutate({ candidateId: candidate.id, payload: {} })}
        className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium bg-red-700 text-white hover:bg-red-800 disabled:opacity-50"
      >
        <XCircle className="h-3 w-3" /> Reject
      </button>
    </div>
  );
}

// ---- Main component --------------------------------------------------------

export default function ExtractionReviewView() {
  const { user } = useAuth();
  const isAdmin = user?.role === "system_admin";
  const { data: institutions } = useInstitutions(true);
  const [selectedId, setSelectedId] = useState("");
  const [activeTab, setActiveTab] = useState<"queue" | "runs" | "candidates">("queue");

  const institutionId = useMemo(() => {
    if (isAdmin) return selectedId || undefined;
    return user?.institution_id ?? undefined;
  }, [isAdmin, selectedId, user]);

  const { data: stats, isLoading: statsLoading } = useExtractionStatistics(institutionId);
  const { data: queue, isLoading: queueLoading } = useReviewQueue(institutionId);
  const { data: runs, isLoading: runsLoading } = useExtractionRuns({ institution_id: institutionId });
  const { data: candidates, isLoading: candidatesLoading } = useExtractionCandidates({ institution_id: institutionId });
  const { data: downloads } = useAcquisitionDownloads(institutionId);
  const triggerExtraction = useTriggerExtraction();

  const tabs = [
    { id: "queue" as const, label: `Review Queue (${queue?.length ?? 0})` },
    { id: "runs" as const, label: `Extraction Runs (${runs?.length ?? 0})` },
    { id: "candidates" as const, label: `All Candidates (${candidates?.length ?? 0})` },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/knowledge/acquisition" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Extraction Review</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Review and approve intelligently extracted academic metadata
          </p>
        </div>
      </div>

      {/* Institution selector (Admin only) */}
      {isAdmin && (
        <div className="max-w-xs">
          <label className="block text-sm font-medium mb-1 text-muted-foreground">Institution</label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">All institutions</option>
            {institutions?.map((i) => (
              <option key={i.id} value={i.id}>{i.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Statistics */}
      {statsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}><CardContent className="p-6"><div className="h-8 bg-muted animate-pulse rounded" /></CardContent></Card>
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatCard label="Total Runs" value={stats.total_runs} />
          <StatCard label="Completed" value={stats.completed_runs} />
          <StatCard label="Needs Review" value={stats.needs_review_runs} sub="runs" />
          <StatCard label="Total Candidates" value={stats.total_candidates} />
          <StatCard label="Awaiting Review" value={stats.needs_review} sub="candidates" />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Select an institution to view extraction statistics.</p>
      )}

      {/* Re-extract from downloaded documents */}
      {downloads && downloads.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Re-run Extraction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Document</th>
                    <th className="pb-2 pr-4 font-medium">Type</th>
                    <th className="pb-2 pr-4 font-medium">Extraction</th>
                    <th className="pb-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {downloads.slice(0, 10).map((doc) => (
                    <tr key={doc.id} className="py-2">
                      <td className="py-2 pr-4">
                        <p className="font-medium truncate max-w-xs">
                          {(doc as any).meaningful_title || doc.title}
                        </p>
                        <p className="text-xs text-muted-foreground truncate max-w-xs">{doc.source_url}</p>
                      </td>
                      <td className="py-2 pr-4">
                        <Badge variant="outline">{doc.document_type}</Badge>
                      </td>
                      <td className="py-2 pr-4">
                        <StatusBadge status={(doc as any).extraction_status ?? "pending"} />
                      </td>
                      <td className="py-2">
                        <button
                          disabled={triggerExtraction.isPending}
                          onClick={() => triggerExtraction.mutate(doc.id)}
                          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium border border-border hover:bg-muted disabled:opacity-50"
                        >
                          <RefreshCw className="h-3 w-3" /> Re-extract
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Review Queue */}
      {activeTab === "queue" && (
        <div>
          {queueLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : !queue || queue.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-600" />
              <p className="font-medium">Review queue is empty</p>
              <p className="text-sm mt-1">All extraction candidates have been reviewed.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Entity Type</th>
                    <th className="pb-2 pr-3 font-medium">Extracted Value</th>
                    <th className="pb-2 pr-3 font-medium">Confidence</th>
                    <th className="pb-2 pr-3 font-medium">Proposed Match</th>
                    <th className="pb-2 pr-3 font-medium">Snippet</th>
                    <th className="pb-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {queue.map((c) => (
                    <tr key={c.id}>
                      <td className="py-3 pr-3"><EntityTypeBadge type={c.entity_type} /></td>
                      <td className="py-3 pr-3 font-medium max-w-[200px] truncate">{c.extracted_value}</td>
                      <td className="py-3 pr-3"><ConfidenceBadge confidence={c.confidence} /></td>
                      <td className="py-3 pr-3 text-muted-foreground text-xs max-w-[160px] truncate">
                        {c.proposed_entity_name ?? "—"}
                        {c.match_method && <span className="ml-1 text-muted-foreground">({c.match_method})</span>}
                      </td>
                      <td className="py-3 pr-3 text-muted-foreground text-xs max-w-[200px] truncate">
                        {c.source_snippet ?? "—"}
                      </td>
                      <td className="py-3"><ReviewActions candidate={c} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Extraction Runs */}
      {activeTab === "runs" && (
        <div>
          {runsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-14 bg-muted animate-pulse rounded" />)}
            </div>
          ) : !runs || runs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p className="font-medium">No extraction runs yet.</p>
              <p className="text-sm mt-1">Start an acquisition job or trigger extraction above.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Run ID</th>
                    <th className="pb-2 pr-3 font-medium">Status</th>
                    <th className="pb-2 pr-3 font-medium">Document Type</th>
                    <th className="pb-2 pr-3 font-medium">Improved Title</th>
                    <th className="pb-2 pr-3 font-medium">Quality</th>
                    <th className="pb-2 pr-3 font-medium">Candidates</th>
                    <th className="pb-2 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td className="py-3 pr-3 font-mono text-xs text-muted-foreground">{r.id.slice(0, 8)}</td>
                      <td className="py-3 pr-3"><StatusBadge status={r.status} /></td>
                      <td className="py-3 pr-3">
                        {r.document_type ? (
                          <Badge variant="outline">{r.document_type.replace(/_/g, " ")}</Badge>
                        ) : "—"}
                      </td>
                      <td className="py-3 pr-3 max-w-[200px] truncate text-xs">
                        {r.improved_title ?? "—"}
                        {r.title_source && <span className="ml-1 text-muted-foreground">({r.title_source})</span>}
                      </td>
                      <td className="py-3 pr-3">
                        {r.extraction_quality ? (
                          <Badge className={QUALITY_STYLES[r.extraction_quality] ?? "bg-muted"}>{r.extraction_quality}</Badge>
                        ) : "—"}
                      </td>
                      <td className="py-3 pr-3 font-semibold">{r.candidates_count}</td>
                      <td className="py-3 text-xs text-muted-foreground">{fmt(r.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* All Candidates */}
      {activeTab === "candidates" && (
        <div>
          {candidatesLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-14 bg-muted animate-pulse rounded" />)}
            </div>
          ) : !candidates || candidates.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p className="font-medium">No candidates found.</p>
              <p className="text-sm mt-1">Run extraction on a downloaded document to generate candidates.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Entity Type</th>
                    <th className="pb-2 pr-3 font-medium">Value</th>
                    <th className="pb-2 pr-3 font-medium">Confidence</th>
                    <th className="pb-2 pr-3 font-medium">Status</th>
                    <th className="pb-2 pr-3 font-medium">Proposed Match</th>
                    <th className="pb-2 font-medium">Data Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {candidates.map((c) => (
                    <tr key={c.id}>
                      <td className="py-3 pr-3"><EntityTypeBadge type={c.entity_type} /></td>
                      <td className="py-3 pr-3 font-medium max-w-[200px] truncate">{c.extracted_value}</td>
                      <td className="py-3 pr-3"><ConfidenceBadge confidence={c.confidence} /></td>
                      <td className="py-3 pr-3"><MappingBadge status={c.mapping_status} /></td>
                      <td className="py-3 pr-3 text-xs text-muted-foreground max-w-[160px] truncate">
                        {c.proposed_entity_name ?? "—"}
                      </td>
                      <td className="py-3">
                        <Badge variant="outline" className="text-xs">{c.data_status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
