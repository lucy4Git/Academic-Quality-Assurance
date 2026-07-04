"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth.store";
import {
  useIkpPackages,
  useIkpChunks,
  useIkpReindex,
  useIkpCreateReviewBatch,
} from "@/hooks/useIkp";
import type { IkpChunk, IkpPackageSummary } from "@/types/ikp";

// ---------------------------------------------------------------------------
// Utility components
// ---------------------------------------------------------------------------

function IndexedBadge({ indexed }: { indexed: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        indexed
          ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300"
          : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300"
      }`}
    >
      {indexed ? "Indexed" : "Not indexed"}
    </span>
  );
}

function EntityTypeBadge({ entityType }: { entityType: string }) {
  const colours: Record<string, string> = {
    programme: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
    module: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
    faculty: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
    department: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300",
    institution: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300",
    admission_requirement: "bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300",
    campus: "bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300",
  };
  const cls = colours[entityType] ?? "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {entityType}
    </span>
  );
}

function ConfidencePct({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colour =
    pct >= 85
      ? "text-green-700 dark:text-green-400"
      : pct >= 70
      ? "text-yellow-700 dark:text-yellow-400"
      : "text-red-600 dark:text-red-400";
  return <span className={`font-medium ${colour}`}>{pct}%</span>;
}

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------

function PackageSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2].map((i) => (
        <div key={i} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
          <div className="h-5 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-3" />
          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
          <div className="h-4 w-64 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chunk detail drawer (inline expand)
// ---------------------------------------------------------------------------

function ChunkRow({ chunk }: { chunk: IkpChunk }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <EntityTypeBadge entityType={chunk.entity_type} />
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {chunk.entity_key || chunk.chunk_id}
          </span>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-2">
          <ConfidencePct value={chunk.confidence_score} />
          <span className="text-gray-400 dark:text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </button>
      {open && (
        <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 bg-gray-50 dark:bg-gray-800/60 space-y-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            <span className="font-medium">Source:</span> {chunk.source_document || "—"}
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {chunk.text}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chunk list panel
// ---------------------------------------------------------------------------

function ChunkListPanel({
  code,
  year,
  version,
  entityTypes,
}: {
  code: string;
  year: string;
  version: string;
  entityTypes: string[];
}) {
  const [entityFilter, setEntityFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading, isError } = useIkpChunks(code, year, version, {
    entityType: entityFilter || undefined,
    skip: page * limit,
    limit,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Filter by type:
        </label>
        <select
          value={entityFilter}
          onChange={(e) => { setEntityFilter(e.target.value); setPage(0); }}
          className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All types</option>
          {entityTypes.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        {data && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {data.total} chunk{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-red-600 dark:text-red-400">Failed to load chunks.</p>
      )}

      {data && data.chunks.length === 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
          No chunks match the selected filter.
        </p>
      )}

      {data && data.chunks.length > 0 && (
        <>
          <div className="space-y-2">
            {data.chunks.map((chunk) => (
              <ChunkRow key={chunk.chunk_id} chunk={chunk} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1.5 text-sm rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Package card
// ---------------------------------------------------------------------------

function PackageCard({ pkg }: { pkg: IkpPackageSummary }) {
  const { user, isAdmin } = useAuthStore((s) => ({
    user: s.user,
    isAdmin: s.isAdmin(),
  }));
  const isQA = useAuthStore((s) => s.isQAOfficer());
  const router = useRouter();

  const [showChunks, setShowChunks] = useState(false);
  const [reindexMsg, setReindexMsg] = useState<string | null>(null);
  const [batchName, setBatchName] = useState(
    `IKP Review — ${pkg.institution_code} ${pkg.academic_year} ${pkg.ikp_version}`
  );
  const [showBatchForm, setShowBatchForm] = useState(false);
  const [batchMsg, setBatchMsg] = useState<string | null>(null);

  const reindex = useIkpReindex(pkg.institution_code, pkg.academic_year, pkg.ikp_version);
  const createBatch = useIkpCreateReviewBatch(
    pkg.institution_code,
    pkg.academic_year,
    pkg.ikp_version
  );

  const entityTypes = Object.keys(pkg.entity_type_breakdown).sort();

  function handleReindex(forceRecreate: boolean) {
    setReindexMsg(null);
    reindex.mutate(
      { force_recreate: forceRecreate },
      {
        onSuccess: (data) => setReindexMsg(`Done: ${data.chunks_indexed} chunks indexed into ${data.collection}.`),
        onError: (err) => setReindexMsg(`Error: ${err.message}`),
      }
    );
  }

  function handleCreateBatch() {
    if (!user?.institution_id) {
      setBatchMsg("Error: your user account has no institution_id.");
      return;
    }
    setBatchMsg(null);
    createBatch.mutate(
      {
        batch_name: batchName,
        institution_id: user.institution_id,
      },
      {
        onSuccess: (data) => {
          setBatchMsg(
            `Batch created: "${data.batch_name}" — ${data.total_items} items. Redirecting to Knowledge Review...`
          );
          setTimeout(() => router.push("/knowledge-review"), 1800);
        },
        onError: (err) => setBatchMsg(`Error: ${err.message}`),
      }
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {pkg.institution_code}
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {pkg.academic_year} · {pkg.ikp_version}
            </span>
            <IndexedBadge indexed={pkg.qdrant_indexed} />
          </div>
          {pkg.qdrant_collection && (
            <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 font-mono">
              Collection: {pkg.qdrant_collection}
            </p>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {pkg.chunk_count}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">chunks</div>
        </div>
      </div>

      {/* Stats row */}
      <div className="border-t border-gray-100 dark:border-gray-700 px-6 py-4 grid grid-cols-3 gap-4 bg-gray-50 dark:bg-gray-800/60">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg confidence</div>
          <ConfidencePct value={pkg.avg_confidence} />
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Min</div>
          <ConfidencePct value={pkg.min_confidence} />
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Max</div>
          <ConfidencePct value={pkg.max_confidence} />
        </div>
      </div>

      {/* Entity type breakdown */}
      <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700">
        <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
          Entity types
        </div>
        <div className="flex flex-wrap gap-2">
          {entityTypes.map((et) => (
            <span
              key={et}
              className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 dark:bg-gray-700 px-2.5 py-1 text-xs text-gray-700 dark:text-gray-300"
            >
              <EntityTypeBadge entityType={et} />
              <span className="font-semibold">{pkg.entity_type_breakdown[et]}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex flex-wrap gap-3 items-center">
        <button
          onClick={() => setShowChunks((v) => !v)}
          className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          {showChunks ? "Hide chunks" : "View chunks"}
        </button>

        {isAdmin && (
          <>
            <button
              onClick={() => handleReindex(false)}
              disabled={reindex.isPending}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 disabled:opacity-50 transition-colors"
            >
              {reindex.isPending ? "Re-indexing…" : "Re-index"}
            </button>
            <button
              onClick={() => handleReindex(true)}
              disabled={reindex.isPending}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-orange-300 dark:border-orange-700 text-orange-700 dark:text-orange-300 hover:bg-orange-50 dark:hover:bg-orange-900/30 disabled:opacity-50 transition-colors"
            >
              Force rebuild
            </button>
          </>
        )}

        {(isAdmin || isQA) && pkg.has_extracted_output && (
          <button
            onClick={() => setShowBatchForm((v) => !v)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            Create review batch
          </button>
        )}

        {(isAdmin || isQA) && !pkg.has_extracted_output && (
          <span className="text-xs text-gray-400 dark:text-gray-500 italic">
            No ADIP extraction — batch creation unavailable for this package.
          </span>
        )}
      </div>

      {/* Reindex feedback */}
      {reindexMsg && (
        <div
          className={`mx-6 mb-4 text-sm rounded-lg px-4 py-2 ${
            reindexMsg.startsWith("Error")
              ? "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300"
              : "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300"
          }`}
        >
          {reindexMsg}
        </div>
      )}

      {/* Create review batch form */}
      {showBatchForm && (
        <div className="mx-6 mb-4 border border-blue-200 dark:border-blue-800 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20 space-y-3">
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Create Knowledge Review batch from{" "}
            <span className="font-mono text-blue-700 dark:text-blue-300">
              {pkg.institution_code}/{pkg.academic_year}/{pkg.ikp_version}
            </span>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Batch name
            </label>
            <input
              type="text"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreateBatch}
              disabled={createBatch.isPending || !batchName.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors"
            >
              {createBatch.isPending ? "Creating…" : "Confirm"}
            </button>
            <button
              onClick={() => { setShowBatchForm(false); setBatchMsg(null); }}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
          {batchMsg && (
            <p
              className={`text-sm rounded px-3 py-2 ${
                batchMsg.startsWith("Error")
                  ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300"
                  : "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
              }`}
            >
              {batchMsg}
            </p>
          )}
        </div>
      )}

      {/* Chunk list */}
      {showChunks && (
        <div className="border-t border-gray-100 dark:border-gray-700 px-6 py-4">
          <ChunkListPanel
            code={pkg.institution_code}
            year={pkg.academic_year}
            version={pkg.ikp_version}
            entityTypes={entityTypes}
          />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function IkpManagementView() {
  const { data: packages, isLoading, isError } = useIkpPackages();

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          IKP Management
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          View Institutional Knowledge Packages, inspect knowledge chunks, check Qdrant
          indexing status, trigger re-indexing, and create Knowledge Review batches.
        </p>
      </div>

      {isLoading && <PackageSkeleton />}

      {isError && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 px-4 py-4 text-sm text-red-700 dark:text-red-300">
          Failed to load IKP packages. Ensure the backend is running and your session is active.
        </div>
      )}

      {packages && packages.length === 0 && (
        <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-6 py-12 text-center">
          <p className="text-gray-500 dark:text-gray-400">
            No IKP packages are available for your institution.
          </p>
        </div>
      )}

      {packages && packages.map((pkg) => (
        <PackageCard
          key={`${pkg.institution_code}-${pkg.academic_year}-${pkg.ikp_version}`}
          pkg={pkg}
        />
      ))}
    </div>
  );
}
