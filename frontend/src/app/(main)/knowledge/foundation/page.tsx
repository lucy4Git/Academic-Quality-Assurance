"use client";

// Institution Knowledge Foundation overview page.
// System Admin can pick any of the 26 SA universities; other roles see their own.

import { useMemo, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useInstitutionCoverage } from "@/hooks/useInstitutionKnowledge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const ENTITY_LABELS: Record<string, string> = {
  campuses: "Campuses",
  faculties: "Faculties",
  schools: "Schools",
  departments: "Departments",
  programmes: "Programmes",
  qualifications: "Qualifications",
  modules: "Modules",
  learning_outcomes: "Learning Outcomes",
  graduate_attributes: "Graduate Attributes",
  policies: "Policies",
  institution_documents: "Documents",
  accreditations: "Accreditations",
  contacts: "Contacts",
};

const PROVENANCE = [
  { key: "public_verified", label: "Public verified", color: "bg-green-500" },
  { key: "needs_review", label: "Needs review", color: "bg-amber-500" },
  { key: "synthetic_demo", label: "Synthetic demo", color: "bg-blue-500" },
  { key: "customer_data", label: "Customer data", color: "bg-purple-500" },
] as const;

export default function KnowledgeFoundationPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "system_admin";
  const { data: institutions } = useInstitutions(true);
  const [selectedId, setSelectedId] = useState<string>("");

  const institutionId = useMemo(() => {
    if (isAdmin) return selectedId || undefined;
    return user?.institution_id ?? undefined;
  }, [isAdmin, selectedId, user?.institution_id]);

  const { data: coverage, isLoading } = useInstitutionCoverage(institutionId);

  const provenanceTotal = coverage
    ? PROVENANCE.reduce(
        (acc, p) => acc + (coverage.provenance[p.key] ?? 0),
        0
      )
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Knowledge Foundation
        </h1>
        <p className="text-muted-foreground">
          Institutional knowledge coverage and data provenance. Synthetic demo
          data is clearly labelled and is never real internal university data.
        </p>
      </div>

      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Institution</CardTitle>
            <CardDescription>
              Select an institution to view its knowledge coverage.
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

      {institutionId && isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      )}

      {coverage && (
        <>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-medium">
              {coverage.institution_code} — {coverage.institution_name}
            </h2>
            {coverage.ready_for_rag ? (
              <Badge className="bg-green-600">Ready for RAG</Badge>
            ) : (
              <Badge variant="secondary">Not RAG-ready</Badge>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(ENTITY_LABELS).map(([key, label]) => (
              <Card key={key}>
                <CardHeader className="pb-2">
                  <CardDescription>{label}</CardDescription>
                  <CardTitle className="text-3xl">
                    {coverage.counts[key] ?? 0}
                  </CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Data provenance</CardTitle>
              <CardDescription>
                Breakdown of how trustworthy the underlying data is.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex h-4 w-full overflow-hidden rounded-full bg-muted">
                {provenanceTotal > 0 &&
                  PROVENANCE.map((p) => {
                    const val = coverage.provenance[p.key] ?? 0;
                    const pct = (val / provenanceTotal) * 100;
                    if (pct === 0) return null;
                    return (
                      <div
                        key={p.key}
                        className={p.color}
                        style={{ width: `${pct}%` }}
                        title={`${p.label}: ${val}`}
                      />
                    );
                  })}
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                {PROVENANCE.map((p) => (
                  <div key={p.key} className="flex items-center gap-2">
                    <span
                      className={`inline-block h-3 w-3 rounded-full ${p.color}`}
                    />
                    <span className="text-muted-foreground">{p.label}:</span>
                    <span className="font-medium">
                      {coverage.provenance[p.key] ?? 0}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
