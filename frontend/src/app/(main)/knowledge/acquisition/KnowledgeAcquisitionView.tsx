"use client";

// Public Knowledge Acquisition Engine — register and crawl official public
// institutional sources. System Admin can target any institution; other staff
// are scoped to their own institution.

import { useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useInstitutions } from "@/hooks/useInstitutions";
import {
  useAcquisitionDownloads,
  useAcquisitionJobs,
  useAcquisitionSources,
  useAcquisitionStatistics,
  useRetryAcquisitionJob,
  useStartAcquisitionJob,
} from "@/hooks/useAcquisition";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-600",
  failed: "bg-red-600",
  running: "bg-amber-500",
  pending: "bg-muted text-foreground",
  cancelled: "bg-muted text-foreground",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <Badge className={STATUS_STYLES[status] ?? "bg-muted text-foreground"}>
      {status}
    </Badge>
  );
}

function fmt(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString();
}

function short(id: string): string {
  return id.slice(0, 8);
}

export function KnowledgeAcquisitionView() {
  const { user } = useAuth();
  const isAdmin = user?.role === "system_admin";
  const { data: institutions } = useInstitutions(true);
  const [selectedId, setSelectedId] = useState<string>("");

  const institutionId = useMemo(() => {
    if (isAdmin) return selectedId || undefined;
    return user?.institution_id ?? undefined;
  }, [isAdmin, selectedId, user?.institution_id]);

  const { data: stats, isLoading: statsLoading } =
    useAcquisitionStatistics(institutionId);
  const { data: sources, isLoading: sourcesLoading } =
    useAcquisitionSources(institutionId);
  const { data: jobs } = useAcquisitionJobs(institutionId);
  const { data: downloads } = useAcquisitionDownloads(institutionId);

  const startJob = useStartAcquisitionJob(institutionId ?? "");
  const retryJob = useRetryAcquisitionJob();

  const canStart =
    !!institutionId &&
    (user?.role === "system_admin" ||
      user?.role === "quality_assurance_officer");

  const statCards: { label: string; value: number | undefined }[] = [
    { label: "Sources", value: stats?.total_sources },
    { label: "Active Sources", value: stats?.active_sources },
    { label: "Total Jobs", value: stats?.total_jobs },
    { label: "Completed", value: stats?.completed_jobs },
    { label: "Failed", value: stats?.failed_jobs },
    { label: "Documents", value: stats?.total_documents },
    { label: "Errors", value: stats?.total_errors },
  ];

  const showData = isAdmin ? !!institutionId : true;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Public Knowledge Acquisition
        </h1>
        <p className="text-muted-foreground">
          Register official public institutional sources and run acquisition
          jobs that respect robots.txt. Only public sources are crawled — no
          internal university data.
        </p>
      </div>

      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Institution</CardTitle>
            <CardDescription>
              Select an institution to manage its acquisition sources.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <select
              className="w-full max-w-md rounded-md border bg-background px-3 py-2 text-sm"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Select an institution…</option>
              {(institutions ?? []).map((inst) => (
                <option key={inst.id} value={inst.id}>
                  {inst.code} — {inst.name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {!institutionId && !isAdmin && (
        <p className="text-sm text-muted-foreground">
          No institution is associated with your account.
        </p>
      )}

      {showData && (
        <>
          {/* Statistics */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {statCards.map((c) => (
              <Card key={c.label}>
                <CardHeader className="pb-2">
                  <CardDescription>{c.label}</CardDescription>
                  <CardTitle className="text-3xl">
                    {statsLoading || c.value === undefined ? "—" : c.value}
                  </CardTitle>
                </CardHeader>
              </Card>
            ))}
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Last Job</CardDescription>
                <CardTitle className="text-base">
                  {statsLoading ? "—" : fmt(stats?.last_job_at ?? null)}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>

          {/* Start acquisition */}
          {canStart && (
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                disabled={startJob.isPending}
                onClick={() => {
                  if (
                    window.confirm(
                      "Start an acquisition job for all active sources of this institution?",
                    )
                  ) {
                    startJob.mutate(undefined);
                  }
                }}
                className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {startJob.isPending ? "Starting…" : "Start Acquisition"}
              </button>
              {startJob.isError && (
                <span className="text-sm text-red-600">
                  {(startJob.error as Error).message}
                </span>
              )}
            </div>
          )}

          {/* Source registry */}
          <Card>
            <CardHeader>
              <CardTitle>Source Registry</CardTitle>
              <CardDescription>
                Official public sources registered for this institution.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sourcesLoading ? (
                <p className="text-sm text-muted-foreground">Loading…</p>
              ) : !sources || sources.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No acquisition sources registered.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="py-2 pr-4 font-medium">Source Name</th>
                        <th className="py-2 pr-4 font-medium">URL</th>
                        <th className="py-2 pr-4 font-medium">Type</th>
                        <th className="py-2 pr-4 font-medium">Status</th>
                        <th className="py-2 pr-4 font-medium">Confidence</th>
                        <th className="py-2 pr-4 font-medium">Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sources.map((s) => (
                        <tr key={s.id} className="border-b last:border-0">
                          <td className="py-2 pr-4">{s.source_name}</td>
                          <td className="py-2 pr-4">
                            <a
                              href={s.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline"
                            >
                              {s.source_url}
                            </a>
                          </td>
                          <td className="py-2 pr-4">{s.source_type}</td>
                          <td className="py-2 pr-4">{s.data_status}</td>
                          <td className="py-2 pr-4">
                            {s.data_confidence ?? "—"}
                          </td>
                          <td className="py-2 pr-4">
                            <Badge
                              className={
                                s.is_active
                                  ? "bg-green-600"
                                  : "bg-muted text-foreground"
                              }
                            >
                              {s.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent jobs */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Jobs</CardTitle>
              <CardDescription>
                Acquisition job runs and their outcomes.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!jobs || jobs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No jobs yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="py-2 pr-4 font-medium">ID</th>
                        <th className="py-2 pr-4 font-medium">Status</th>
                        <th className="py-2 pr-4 font-medium">Documents</th>
                        <th className="py-2 pr-4 font-medium">Errors</th>
                        <th className="py-2 pr-4 font-medium">Started</th>
                        <th className="py-2 pr-4 font-medium">Completed</th>
                        <th className="py-2 pr-4 font-medium"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.map((j) => (
                        <tr key={j.id} className="border-b last:border-0">
                          <td className="py-2 pr-4 font-mono">{short(j.id)}</td>
                          <td className="py-2 pr-4">
                            <StatusBadge status={j.status} />
                          </td>
                          <td className="py-2 pr-4">{j.documents_downloaded}</td>
                          <td className="py-2 pr-4">{j.errors_count}</td>
                          <td className="py-2 pr-4">{fmt(j.started_at)}</td>
                          <td className="py-2 pr-4">{fmt(j.completed_at)}</td>
                          <td className="py-2 pr-4">
                            {j.status === "failed" && canStart && (
                              <button
                                type="button"
                                onClick={() => retryJob.mutate(j.id)}
                                disabled={retryJob.isPending}
                                className="rounded-md border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50"
                              >
                                Retry
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Downloaded documents */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Downloaded Documents</CardTitle>
                <CardDescription>
                  Documents acquired from registered sources. Wave 3 extraction runs automatically after download.
                </CardDescription>
              </div>
              {institutionId && (
                <Link
                  href="/knowledge/acquisition/extraction"
                  className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                >
                  Extraction Review →
                </Link>
              )}
            </CardHeader>
            <CardContent>
              {!downloads || downloads.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No documents downloaded yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="py-2 pr-4 font-medium">Title</th>
                        <th className="py-2 pr-4 font-medium">File Type</th>
                        <th className="py-2 pr-4 font-medium">Doc Type</th>
                        <th className="py-2 pr-4 font-medium">Extraction</th>
                        <th className="py-2 pr-4 font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {downloads.map((d) => (
                        <tr key={d.id} className="border-b last:border-0">
                          <td className="py-2 pr-4">
                            <p className="font-medium">{d.meaningful_title || d.title}</p>
                            {d.meaningful_title && d.meaningful_title !== d.title && (
                              <p className="text-xs text-muted-foreground">orig: {d.title}</p>
                            )}
                          </td>
                          <td className="py-2 pr-4">{d.file_type}</td>
                          <td className="py-2 pr-4">
                            <Badge variant="outline">{d.document_type}</Badge>
                          </td>
                          <td className="py-2 pr-4">
                            <Badge className={
                              d.extraction_status === "completed" ? "bg-green-600" :
                              d.extraction_status === "failed" ? "bg-red-600" :
                              d.extraction_status === "running" ? "bg-amber-500" :
                              "bg-muted text-foreground"
                            }>
                              {d.extraction_status ?? "pending"}
                            </Badge>
                          </td>
                          <td className="py-2 pr-4">{fmt(d.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
