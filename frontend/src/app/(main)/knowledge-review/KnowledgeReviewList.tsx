"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, RefreshCw, Database } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ReviewStatusBadge } from "@/components/knowledge-review/ReviewStatusBadge";
import {
  useKnowledgeReviewBatches,
  useCreateBatchFromADIP,
} from "@/hooks/useKnowledgeReview";
import { useAuthStore } from "@/store/auth.store";
import type { KnowledgeReviewBatchSummary } from "@/types/knowledge-review";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function KnowledgeReviewList() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data: batches, isLoading, refetch } = useKnowledgeReviewBatches();
  const createFromADIP = useCreateBatchFromADIP();

  const handleCreateFromADIP = async () => {
    if (!user?.institution_id) {
      toast.error("Institution not found. Please log in again.");
      return;
    }
    try {
      const batch = await createFromADIP.mutateAsync({
        institution_id: user.institution_id,
        batch_name: `TUT ICT 2026 v1.1.0 – ${new Date().toLocaleDateString("en-ZA")}`,
        ikp_version: "1.1.0",
        academic_year: "2026",
        faculty_scope: "Faculty of Information and Communication Technology",
        source_extraction_dir: "ikp/institutions/tut/2026/v1.1.0/extracted",
      });
      toast.success(`Batch created with ${batch.total_items} items.`);
      router.push(`/knowledge-review/${batch.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create batch.");
    }
  };

  const filtered =
    statusFilter === "all"
      ? (batches ?? [])
      : (batches ?? []).filter((b) => b.status === statusFilter);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Knowledge Review Centre
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review and approve extracted academic knowledge before it enters the
            institutional knowledge base.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={handleCreateFromADIP}
            disabled={createFromADIP.isPending}
          >
            <Database className="h-4 w-4" />
            {createFromADIP.isPending ? "Creating…" : "Load TUT ICT 2026 Batch"}
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        {(["all", "open", "in_review", "approved", "exported", "closed"] as const).map(
          (s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={
                statusFilter === s
                  ? "px-3 py-1 rounded-full text-xs font-medium bg-primary text-primary-foreground"
                  : "px-3 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground hover:text-foreground"
              }
            >
              {s === "all" ? "All" : s.replace("_", " ")}
            </button>
          )
        )}
        <span className="ml-2 text-xs text-muted-foreground">
          {filtered.length} batch{filtered.length !== 1 ? "es" : ""}
        </span>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center space-y-4">
          <Database className="h-12 w-12 text-muted-foreground/40" />
          <p className="text-muted-foreground text-sm">
            No review batches found. Click &ldquo;Load TUT ICT 2026 Batch&rdquo; to create one
            from the ADIP extraction output.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Batch Name
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Version
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Total
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Approved
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Rejected
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Pending
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Created
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((batch: KnowledgeReviewBatchSummary) => (
                <tr key={batch.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <Link
                      href={`/knowledge-review/${batch.id}`}
                      className="font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {batch.batch_name}
                    </Link>
                    {batch.faculty_scope && (
                      <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-xs">
                        {batch.faculty_scope}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                    {batch.academic_year} / v{batch.ikp_version}
                  </td>
                  <td className="px-4 py-3">
                    <ReviewStatusBadge status={batch.status} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs">
                    {batch.total_items}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-green-700">
                    {batch.approved_count}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-red-700">
                    {batch.rejected_count}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-blue-700">
                    {batch.pending_count}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {formatDate(batch.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/knowledge-review/${batch.id}`}>
                      <Button variant="outline" size="sm">
                        Review
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
