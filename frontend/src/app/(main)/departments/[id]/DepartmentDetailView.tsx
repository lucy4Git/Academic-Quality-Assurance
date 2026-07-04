"use client";

import Link from "next/link";
import {
  BookOpen,
  Pencil,
  GraduationCap,
  Calendar,
  Layers,
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
import { useDepartment } from "@/hooks/useDepartments";
import { useFaculty } from "@/hooks/useFaculties";

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
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
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

export function DepartmentDetailView({ id }: Props) {
  const { data: dept, isLoading, isError, refetch } = useDepartment(id);
  const { data: faculty } = useFaculty(dept?.faculty_id ?? "");

  if (isLoading) return <DetailSkeleton />;

  if (isError || !dept) {
    return (
      <ErrorState
        title="Department not found"
        message="This department does not exist or you don't have access to it."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={dept.name}
        subtitle={
          faculty
            ? `${dept.code} · ${faculty.name} (${faculty.code})`
            : dept.code
        }
        actions={
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
              "head_of_department",
            ]}
          >
            <Link
              href={`/departments/${id}/edit`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Link>
          </RoleGuard>
        }
      />

      {/* Stat cards — deferred to Phase 3 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard icon={Layers} label="Programmes" value="—" />
        <StatCard icon={Boxes} label="Modules" value="—" />
        <StatCard icon={FileText} label="Avg Compliance" value="—" />
      </div>

      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="programmes">Programmes</TabsTrigger>
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <TabsTrigger value="findings">Findings</TabsTrigger>
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
              "head_of_department",
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
                  Department Profile
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="h-7 w-7 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground truncate">
                      {dept.name}
                    </p>
                    <Badge
                      variant="secondary"
                      className="font-mono text-xs mt-1"
                    >
                      {dept.code}
                    </Badge>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  {faculty && (
                    <MetaRow
                      icon={GraduationCap}
                      label="Faculty"
                      value={`${faculty.name} (${faculty.code})`}
                    />
                  )}
                  {faculty?.campus && (
                    <MetaRow
                      icon={GraduationCap}
                      label="Campus"
                      value={faculty.campus}
                    />
                  )}
                  <MetaRow
                    icon={Calendar}
                    label="Added"
                    value={formatDate(dept.created_at)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">
                  Recent Activity
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

        {/* Programmes — Phase 2 Step 4 */}
        <TabsContent value="programmes" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <Layers className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Programme management is implemented in Phase 2 Step 4.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Navigate to{" "}
                <Link href="/programmes" className="text-primary hover:underline">
                  Programmes
                </Link>{" "}
                to see all programmes.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Modules — Phase 2 Step 5 */}
        <TabsContent value="modules" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <Boxes className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Module management is implemented in Phase 2 Step 5.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Findings */}
        <TabsContent value="findings" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                Department-scoped findings will appear here.
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Available in Phase 2 Findings Management.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings" className="pt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Department Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex justify-between py-2 border-b">
                  <span>Department ID</span>
                  <span className="font-mono text-xs text-foreground">
                    {dept.id}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Faculty ID</span>
                  <span className="font-mono text-xs text-foreground">
                    {dept.faculty_id}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Created</span>
                  <span className="text-foreground">
                    {formatDateTime(dept.created_at)}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span>Last updated</span>
                  <span className="text-foreground">
                    {formatDateTime(dept.updated_at)}
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <Link
                  href={`/departments/${id}/edit`}
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" })
                  )}
                >
                  <Pencil className="mr-1.5 h-3.5 w-3.5" />
                  Edit Department
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
