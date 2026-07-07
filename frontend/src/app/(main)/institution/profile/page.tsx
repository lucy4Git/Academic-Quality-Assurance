"use client";

// Institution profile page — full profile assembled from the Wave 1 knowledge
// foundation: campuses, faculties, policies, documents, accreditations, contacts.
// System Admin can pick any institution; other roles see their own.

import { useMemo, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useFullInstitutionProfile } from "@/hooks/useInstitutionKnowledge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

function ProvenanceBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    public_verified: "bg-green-600",
    needs_review: "bg-amber-500",
    synthetic_demo: "bg-blue-500",
    customer_data: "bg-purple-600",
  };
  return (
    <Badge className={map[status] ?? "bg-muted"}>
      {status.replace(/_/g, " ")}
    </Badge>
  );
}

export default function InstitutionProfilePage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "system_admin";
  const { data: institutions } = useInstitutions();
  const [selectedId, setSelectedId] = useState<string>("");

  const institutionId = useMemo(() => {
    if (isAdmin) return selectedId || undefined;
    return user?.institution_id ?? undefined;
  }, [isAdmin, selectedId, user?.institution_id]);

  const { data: profile, isLoading } = useFullInstitutionProfile(institutionId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Institution Profile
        </h1>
        <p className="text-muted-foreground">
          Full institutional knowledge profile. Provenance badges show how
          trustworthy each record is.
        </p>
      </div>

      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Institution</CardTitle>
            <CardDescription>
              Select an institution to view its full profile.
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

      {institutionId && (isLoading || !profile) && (
        <Skeleton className="h-64 w-full" />
      )}

      {profile && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-xl font-semibold tracking-tight">
              {profile.name}
            </h2>
            <Badge variant="secondary">{profile.code}</Badge>
            {profile.data_status && (
              <ProvenanceBadge status={profile.data_status} />
            )}
            {profile.is_demo && <Badge variant="outline">Demo data</Badge>}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Overview</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
              <div>
                <span className="text-muted-foreground">Province: </span>
                {profile.province ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">Country: </span>
                {profile.country ?? "—"}
              </div>
              <div>
                <span className="text-muted-foreground">Website: </span>
                {profile.website ? (
                  <a
                    href={profile.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary underline"
                  >
                    {profile.website}
                  </a>
                ) : (
                  "—"
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Campuses</CardTitle>
              <CardDescription>
                {profile.campuses.length} campus(es)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.campuses.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium">{c.name}</span>
                    {c.is_main_campus && (
                      <Badge variant="outline" className="ml-2">
                        Main
                      </Badge>
                    )}
                    <div className="text-xs text-muted-foreground">
                      {[c.city, c.province].filter(Boolean).join(", ") || "—"}
                    </div>
                  </div>
                  <ProvenanceBadge status={c.data_status} />
                </div>
              ))}
              {profile.campuses.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No campuses listed.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Faculties</CardTitle>
              <CardDescription>
                {profile.faculties.length} faculty(ies)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.faculties.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium">{f.name}</span>
                    <div className="text-xs text-muted-foreground">
                      {f.code}
                    </div>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {f.department_count} dept(s)
                  </span>
                </div>
              ))}
              {profile.faculties.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No faculties listed.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Policies</CardTitle>
              <CardDescription>
                {profile.policies.length} recent policy(ies)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.policies.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium">{p.title}</span>
                    <div className="text-xs text-muted-foreground">
                      {p.policy_type ?? "—"}
                    </div>
                  </div>
                  <ProvenanceBadge status={p.data_status} />
                </div>
              ))}
              {profile.policies.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No policies recorded.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Documents</CardTitle>
              <CardDescription>
                {profile.documents.length} recent document(s)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.documents.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium">{d.title}</span>
                    <div className="text-xs text-muted-foreground">
                      {[d.document_type, d.publication_year]
                        .filter(Boolean)
                        .join(" · ") || "—"}
                    </div>
                  </div>
                  <ProvenanceBadge status={d.data_status} />
                </div>
              ))}
              {profile.documents.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No documents recorded.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contacts</CardTitle>
              <CardDescription>Institutional contacts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.contacts.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium">
                      {c.name ?? c.role ?? "—"}
                    </span>
                    <div className="text-xs text-muted-foreground">
                      {c.email ?? "—"}
                    </div>
                  </div>
                  <ProvenanceBadge status={c.data_status} />
                </div>
              ))}
              {profile.contacts.length === 0 && (
                <p className="text-sm text-muted-foreground">No contacts.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Accreditations</CardTitle>
              <CardDescription>
                {profile.accreditations.length} record(s)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {profile.accreditations.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between border-b py-2 last:border-0"
                >
                  <div>
                    <span className="font-medium capitalize">{a.status}</span>
                    <div className="text-xs text-muted-foreground">
                      {a.expiry_date ? `Expires ${a.expiry_date}` : "—"}
                    </div>
                  </div>
                  <ProvenanceBadge status={a.data_status} />
                </div>
              ))}
              {profile.accreditations.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No accreditations recorded.
                </p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
