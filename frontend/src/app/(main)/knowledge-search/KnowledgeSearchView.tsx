"use client";

import { useState } from "react";
import { Search, AlertCircle, BookOpen, Layers, Building2, FileText, Info } from "lucide-react";
import { useKnowledgeSearch } from "@/hooks/useKnowledgeSearch";
import { useAuthStore } from "@/store/auth.store";
import { useInstitutions } from "@/hooks/useInstitutions";
import { extractErrorMessage } from "@/lib/api-client";
import type { SearchResult } from "@/types/knowledge-index";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ENTITY_TYPE_OPTIONS = [
  { value: "", label: "All types" },
  { value: "programme", label: "Programme" },
  { value: "module", label: "Module" },
  { value: "faculty", label: "Faculty" },
  { value: "department", label: "Department" },
  { value: "institution", label: "Institution" },
  { value: "admission_requirement", label: "Admission Requirement" },
  { value: "campus", label: "Campus" },
];

const ENTITY_TYPE_ICONS: Record<string, typeof BookOpen> = {
  programme: Layers,
  module: BookOpen,
  faculty: Building2,
  department: BookOpen,
  institution: Building2,
  admission_requirement: FileText,
  campus: Building2,
};

// ---------------------------------------------------------------------------
// Confidence badge
// ---------------------------------------------------------------------------

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  let cls = "bg-green-100 text-green-800";
  if (pct < 70) cls = "bg-red-100 text-red-800";
  else if (pct < 85) cls = "bg-yellow-100 text-yellow-800";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {pct}% confidence
    </span>
  );
}

// ---------------------------------------------------------------------------
// Entity type badge
// ---------------------------------------------------------------------------

function EntityTypeBadge({ entityType }: { entityType: string }) {
  const label = entityType.replace(/_/g, " ");
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 capitalize">
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Result card
// ---------------------------------------------------------------------------

function ResultCard({ result, rank }: { result: SearchResult; rank: number }) {
  const Icon = ENTITY_TYPE_ICONS[result.entity_type] ?? FileText;
  const relevancePct = Math.round(result.score * 100);

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
            <Icon className="h-4 w-4 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-card-foreground truncate">
              #{rank} {result.title || result.entity_id}
            </p>
            <p className="text-xs text-muted-foreground">{result.institution_code} · {result.academic_year}</p>
          </div>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2">
          <EntityTypeBadge entityType={result.entity_type} />
          <ConfidenceBadge score={result.confidence_score} />
        </div>
      </div>

      {/* Text */}
      <p className="text-sm text-card-foreground leading-relaxed line-clamp-4">
        {result.text}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-muted-foreground border-t border-border pt-2">
        <span>Relevance: {relevancePct}%</span>
        {result.source_document && (
          <span className="truncate max-w-[60%]">Source: {result.source_document}</span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Search className="h-12 w-12 text-muted-foreground/30 mb-4" />
      <p className="text-sm font-medium text-muted-foreground">
        Enter a query to search the knowledge base
      </p>
      <p className="text-xs text-muted-foreground mt-1">
        Search programmes, modules, faculties, and more
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// No results state
// ---------------------------------------------------------------------------

function NoResultsState({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Search className="h-12 w-12 text-muted-foreground/30 mb-4" />
      <p className="text-sm font-medium text-muted-foreground">
        No results for &ldquo;{query}&rdquo;
      </p>
      <p className="text-xs text-muted-foreground mt-1">
        Try different keywords or broaden the entity type filter
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function KnowledgeSearchView() {
  const user = useAuthStore((s) => s.user);
  const isSysAdmin = user?.role === "system_admin";

  const { data: institutions } = useInstitutions();
  const activePilots = institutions?.filter((i) => i.is_active && i.institution_type === "pilot") ?? [];

  const [query, setQuery] = useState("");
  const [institutionCode, setInstitutionCode] = useState<string>(
    isSysAdmin ? "" : ""   // will be resolved from user's institution on submit
  );
  const [entityType, setEntityType] = useState("");
  const [topK, setTopK] = useState(10);
  const [minConfidence, setMinConfidence] = useState(0);
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null);

  const { mutate, data, isPending, isError, error, reset } = useKnowledgeSearch();

  // Resolve effective institution code for non-admin users
  const effectiveCode = isSysAdmin
    ? institutionCode
    : activePilots.find((i) => i.id === user?.institution_id)?.code ?? "";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    if (!effectiveCode) return;

    setSubmittedQuery(query.trim());
    reset();
    mutate({
      query: query.trim(),
      institution_code: effectiveCode,
      entity_type: entityType || undefined,
      top_k: topK,
      min_confidence: minConfidence,
    });
  }

  const hasResults = data && data.total_results > 0;
  const isEmpty = data && data.total_results === 0 && submittedQuery;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Knowledge Search</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Semantic search over indexed institutional knowledge packages
        </p>
      </div>

      {/* Dev placeholder warning */}
      {data?.is_placeholder_embedding && (
        <div className="flex items-start gap-2 rounded-md border border-yellow-300 bg-yellow-50 px-4 py-3 text-sm text-yellow-800">
          <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <p>
            <strong>Development mode:</strong> Using hash-based placeholder embeddings.
            Results are ranked by hash similarity, not semantic meaning.
            Replace the embedding service for production use.
          </p>
        </div>
      )}

      {/* Search form */}
      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-4 space-y-4">
        {/* Query input */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What are the admission requirements for Computer Science?"
              className="w-full pl-9 pr-4 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            />
          </div>
          <button
            type="submit"
            disabled={isPending || !query.trim() || !effectiveCode}
            className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            {isPending ? "Searching…" : "Search"}
          </button>
        </div>

        {/* Filters row */}
        <div className="flex flex-wrap gap-3">
          {/* Institution selector — System Admin only */}
          {isSysAdmin && (
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-muted-foreground">Institution</label>
              <select
                value={institutionCode}
                onChange={(e) => setInstitutionCode(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                aria-label="Select institution"
              >
                <option value="">— select institution —</option>
                {activePilots.map((inst) => (
                  <option key={inst.id} value={inst.code}>
                    {inst.code} — {inst.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Entity type filter */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">Entity type</label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label="Filter by entity type"
            >
              {ENTITY_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Top K */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">Results</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label="Number of results"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>

          {/* Min confidence */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">Min confidence</label>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label="Minimum confidence"
            >
              <option value={0}>Any</option>
              <option value={0.7}>70%+</option>
              <option value={0.85}>85%+</option>
              <option value={0.9}>90%+</option>
            </select>
          </div>
        </div>

        {/* Institution locked indicator for non-admin */}
        {!isSysAdmin && effectiveCode && (
          <p className="text-xs text-muted-foreground">
            Searching: <span className="font-medium text-foreground">{effectiveCode}</span>
            {" "}(your institution)
          </p>
        )}
        {!isSysAdmin && !effectiveCode && (
          <p className="text-xs text-destructive">
            Your account is not associated with an active pilot institution.
          </p>
        )}
      </form>

      {/* Error state */}
      {isError && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <p>{extractErrorMessage(error)}</p>
        </div>
      )}

      {/* Loading state */}
      {isPending && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-md bg-muted" />
                <div className="space-y-1 flex-1">
                  <div className="h-3 bg-muted rounded w-1/3" />
                  <div className="h-2 bg-muted rounded w-1/4" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-2 bg-muted rounded" />
                <div className="h-2 bg-muted rounded w-5/6" />
                <div className="h-2 bg-muted rounded w-4/6" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results header */}
      {data && !isPending && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {data.total_results} result{data.total_results !== 1 ? "s" : ""} for{" "}
            <span className="font-medium text-foreground">&ldquo;{data.query}&rdquo;</span>
            {" "}in <span className="font-medium text-foreground">{data.institution_code}</span>
          </p>
          <span className="text-xs text-muted-foreground">
            Model: {data.embedding_model}
          </span>
        </div>
      )}

      {/* Result cards */}
      {hasResults && !isPending && (
        <div className="space-y-3">
          {data.results.map((result, i) => (
            <ResultCard key={`${result.entity_id}-${i}`} result={result} rank={i + 1} />
          ))}
        </div>
      )}

      {/* No results */}
      {isEmpty && !isPending && submittedQuery && <NoResultsState query={submittedQuery} />}

      {/* Initial empty state */}
      {!data && !isPending && !isError && <EmptyState />}
    </div>
  );
}
