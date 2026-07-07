"use client";

// Institution profile page — public details, campuses, public contacts, accreditations.

import { useAuth } from "@/hooks/useAuth";
import { useInstitutionKnowledgeProfile } from "@/hooks/useInstitutionKnowledge";
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
  const { data: profile, isLoading } = useInstitutionKnowledgeProfile(
    user?.institution_id ?? undefined
  );

  if (!user?.institution_id) {
    return (
      <p className="text-sm text-muted-foreground">
        No institution is associated with your account.
      </p>
    );
  }

  if (isLoading || !profile) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          {profile.name}
        </h1>
        <Badge variant="secondary">{profile.code}</Badge>
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
          <CardDescription>{profile.campuses.length} campus(es)</CardDescription>
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
            <p className="text-sm text-muted-foreground">No campuses listed.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Contacts</CardTitle>
          <CardDescription>Public institutional contacts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {profile.contacts.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between border-b py-2 last:border-0"
            >
              <div>
                <span className="font-medium">{c.name ?? c.role ?? "—"}</span>
                <div className="text-xs text-muted-foreground">
                  {c.email ?? "—"}
                </div>
              </div>
              <ProvenanceBadge status={c.data_status} />
            </div>
          ))}
          {profile.contacts.length === 0 && (
            <p className="text-sm text-muted-foreground">No public contacts.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Accreditations</CardTitle>
          <CardDescription>{profile.accreditations.length} record(s)</CardDescription>
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
    </div>
  );
}
