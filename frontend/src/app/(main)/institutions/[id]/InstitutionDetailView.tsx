"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  Pencil,
  MapPin,
  Globe,
  Calendar,
  GraduationCap,
  BookOpen,
  Layers,
  Boxes,
  Users,
  FileText,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { buttonVariants } from "@/components/ui/button";
import { cn, formatDate, formatDateTime } from "@/lib/utils";
import { useInstitution, useInstitutionStats } from "@/hooks/useInstitutions";

interface Props {
  id: string;
}

// ── Loading skeleton ───────────────────────────────────────────────────────────
function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-8 w-20" />
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}

// ── Stat card ──────────────────────────────────────────────────────────────────
function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-2">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-xs font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
    </div>
  );
}

// ── Meta row ──────────────────────────────────────────────────────────────────
function MetaRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | null | undefined;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3">
      <Icon className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm text-foreground mt-0.5 break-words">{value}</p>
      </div>
    </div>
  );
}

export function InstitutionDetailView({ id }: Props) {
  const router = useRouter();
  const { data: institution, isLoading, isError, refetch } = useInstitution(id);
  const { data: stats } = useInstitutionStats(id);

  if (isLoading) return <DetailSkeleton />;

  if (isError || !institution) {
    return (
      <ErrorState
        title="Institution not found"
        message="This institution does not exist or you don't have access to it."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <PageHeader
        title={institution.name}
        subtitle={`Code: ${institution.code}`}
        actions={
          <RoleGuard roles={["system_admin"]}>
            <Link
              href={`/institutions/${id}/edit`}
              className={cn(
                buttonVariants({ variant: "outline", size: "sm" })
              )}
            >
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Link>
          </RoleGuard>
        }
      />

      {/* Stat row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard icon={GraduationCap} label="Faculties" value={stats?.faculties ?? "—"} />
        <StatCard icon={BookOpen} label="Departments" value={stats?.departments ?? "—"} />
        <StatCard icon={Layers} label="Programmes" value={stats?.programmes ?? "—"} />
        <StatCard icon={Boxes} label="Modules" value={stats?.modules ?? "—"} />
        <StatCard icon={Users} label="Users" value={stats?.users ?? "—"} />
        <StatCard icon={FileText} label="Files" value={stats?.files ?? "—"} />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="faculties">Faculties</TabsTrigger>
          <TabsTrigger value="findings">Findings</TabsTrigger>
          <RoleGuard roles={["system_admin"]}>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </RoleGuard>
        </TabsList>

        {/* ── Overview ─────────────────────────────────────────────────────── */}
        <TabsContent value="overview" className="pt-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Institution profile card */}
            <Card className="lg:col-span-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">
                  Institution Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Logo / avatar */}
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {institution.logo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={institution.logo_url}
                        alt={institution.name}
                        className="w-12 h-12 object-contain rounded-lg"
                      />
                    ) : (
                      <Building2 className="h-7 w-7 text-primary" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground truncate">
                      {institution.name}
                    </p>
                    <Badge variant="secondary" className="font-mono text-xs mt-1">
                      {institution.code}
                    </Badge>
                  </div>
                </div>

                <Separator />

                <div className="space-y-3">
                  <MetaRow
                    icon={Globe}
                    label="Country"
                    value={institution.country}
                  />
                  <MetaRow
                    icon={MapPin}
                    label="Address"
                    value={institution.address}
                  />
                  <MetaRow
                    icon={Calendar}
                    label="Registered"
                    value={formatDate(institution.created_at)}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Recent activity placeholder */}
            <Card className="lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">
                  Recent Audit Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <FileText className="h-8 w-8 text-muted-foreground/40 mb-3" />
                  <p className="text-sm text-muted-foreground">
                    Audit activity will appear here once audits are triggered.
                  </p>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    Available in Phase 2 Audit Management.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Faculties ────────────────────────────────────────────────────── */}
        <TabsContent value="faculties" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <GraduationCap className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Faculty management is implemented in Phase 2 Step 2.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Navigate to{" "}
                <Link
                  href="/faculties"
                  className="text-primary hover:underline"
                >
                  Faculties
                </Link>{" "}
                to see all faculties for this institution.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Findings ─────────────────────────────────────────────────────── */}
        <TabsContent value="findings" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Findings for this institution will appear here.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Available in Phase 2 Findings Management.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Settings (SA only) ───────────────────────────────────────────── */}
        <TabsContent value="settings" className="pt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Institution Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex justify-between py-2 border-b">
                  <span>Institution ID</span>
                  <span className="font-mono text-xs text-foreground">
                    {institution.id}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Created</span>
                  <span className="text-foreground">
                    {formatDateTime(institution.created_at)}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Last updated</span>
                  <span className="text-foreground">
                    {formatDateTime(institution.updated_at)}
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <Link
                  href={`/institutions/${id}/edit`}
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" })
                  )}
                >
                  <Pencil className="mr-1.5 h-3.5 w-3.5" />
                  Edit Institution
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
