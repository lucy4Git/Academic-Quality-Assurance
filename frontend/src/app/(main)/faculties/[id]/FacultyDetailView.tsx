"use client";

import Link from "next/link";
import {
  GraduationCap,
  Pencil,
  MapPin,
  Building2,
  Calendar,
  BookOpen,
  Boxes,
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
import { useFaculty } from "@/hooks/useFaculties";
import { useInstitutions } from "@/hooks/useInstitutions";

interface Props {
  id: string;
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-56" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-8 w-16" />
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

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
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
    </div>
  );
}

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
        <p className="text-sm text-foreground mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export function FacultyDetailView({ id }: Props) {
  const { data: faculty, isLoading, isError, refetch } = useFaculty(id);
  const { data: institutions } = useInstitutions();

  const institutionName = institutions?.find(
    (i) => i.id === faculty?.institution_id
  )?.name;

  if (isLoading) return <DetailSkeleton />;

  if (isError || !faculty) {
    return (
      <ErrorState
        title="Faculty not found"
        message="This faculty does not exist or you don't have access to it."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={faculty.name}
        subtitle={
          institutionName
            ? `${faculty.code} · ${institutionName}`
            : faculty.code
        }
        actions={
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
            ]}
          >
            <Link
              href={`/faculties/${id}/edit`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Link>
          </RoleGuard>
        }
      />

      {/* Campus badge in header */}
      {faculty.campus && (
        <div className="-mt-4">
          <Badge variant="outline" className="gap-1">
            <MapPin className="h-3 w-3" />
            {faculty.campus}
          </Badge>
        </div>
      )}

      {/* Stat cards — counts deferred to Phase 3 dashboard endpoint */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatCard icon={BookOpen} label="Departments" value="—" />
        <StatCard icon={Boxes} label="Modules" value="—" />
        <StatCard icon={FileText} label="Avg Compliance" value="—" />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="departments">Departments</TabsTrigger>
          <TabsTrigger value="findings">Findings</TabsTrigger>
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
            ]}
          >
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </RoleGuard>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="pt-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">
                  Faculty Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <GraduationCap className="h-7 w-7 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground truncate">
                      {faculty.name}
                    </p>
                    <Badge
                      variant="secondary"
                      className="font-mono text-xs mt-1"
                    >
                      {faculty.code}
                    </Badge>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  {institutionName && (
                    <MetaRow
                      icon={Building2}
                      label="Institution"
                      value={institutionName}
                    />
                  )}
                  <MetaRow
                    icon={MapPin}
                    label="Campus"
                    value={faculty.campus}
                  />
                  <MetaRow
                    icon={Calendar}
                    label="Added"
                    value={formatDate(faculty.created_at)}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Placeholder: recent audit activity */}
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
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Departments — Phase 2 Step 3 */}
        <TabsContent value="departments" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <BookOpen className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Department management is implemented in Phase 2 Step 3.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Navigate to{" "}
                <Link href="/departments" className="text-primary hover:underline">
                  Departments
                </Link>{" "}
                to see all departments.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Findings — Phase 2 Findings step */}
        <TabsContent value="findings" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Faculty-scoped findings will appear here.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Available in Phase 2 Findings Management.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings — QA+Dean */}
        <TabsContent value="settings" className="pt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Faculty Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex justify-between py-2 border-b">
                  <span>Faculty ID</span>
                  <span className="font-mono text-xs text-foreground">
                    {faculty.id}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Institution ID</span>
                  <span className="font-mono text-xs text-foreground">
                    {faculty.institution_id}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Created</span>
                  <span className="text-foreground">
                    {formatDateTime(faculty.created_at)}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Last updated</span>
                  <span className="text-foreground">
                    {formatDateTime(faculty.updated_at)}
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <Link
                  href={`/faculties/${id}/edit`}
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" })
                  )}
                >
                  <Pencil className="mr-1.5 h-3.5 w-3.5" />
                  Edit Faculty
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
