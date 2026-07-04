"use client";

import Link from "next/link";
import {
  Boxes,
  Pencil,
  Calendar,
  Layers,
  BookOpen,
  Award,
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
import { useModule } from "@/hooks/useModules";
import { useProgramme } from "@/hooks/useProgrammes";

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
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
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

function PlaceholderTab({ label }: { label: string }) {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <Boxes className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">
          {label} will be available in a later AQAA phase.
        </p>
      </CardContent>
    </Card>
  );
}

export function ModuleDetailView({ id }: { id: string }) {
  const { data: mod, isLoading, isError, refetch } = useModule(id);
  const { data: programme } = useProgramme(mod?.programme_id ?? "");

  if (isLoading) return <DetailSkeleton />;
  if (isError || !mod) {
    return (
      <ErrorState
        title="Module not found"
        message="This module does not exist or you don't have access to it."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={mod.name}
        subtitle={`${mod.code} · ${programme?.name ?? "—"}`}
        actions={
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
              "head_of_department",
              "programme_coordinator",
            ]}
          >
            <Link
              href={`/modules/${id}/edit`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Link>
          </RoleGuard>
        }
      />

      {/* Quick stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard icon={Award} label="Credits" value={mod.credits} />
        <StatCard icon={Calendar} label="Semester" value={mod.semester} />
        <StatCard icon={Calendar} label="Academic Year" value={mod.academic_year} />
        <StatCard icon={Layers} label="Programme" value={programme?.code ?? "—"} />
      </div>

      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="assessments">Assessments</TabsTrigger>
          <TabsTrigger value="moderation">Moderation</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="audits">Audits</TabsTrigger>
          <RoleGuard
            roles={[
              "system_admin",
              "quality_assurance_officer",
              "faculty_dean",
              "head_of_department",
              "programme_coordinator",
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
                <CardTitle className="text-sm font-medium">Module Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Boxes className="h-7 w-7 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground truncate">{mod.name}</p>
                    <Badge variant="secondary" className="font-mono text-xs mt-1">
                      {mod.code}
                    </Badge>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  {programme && (
                    <MetaRow
                      icon={Layers}
                      label="Programme"
                      value={`${programme.name} (${programme.code})`}
                    />
                  )}
                  <MetaRow icon={Award} label="Credits" value={`${mod.credits} credits`} />
                  <MetaRow icon={Calendar} label="Semester" value={mod.semester} />
                  <MetaRow icon={Calendar} label="Academic Year" value={mod.academic_year} />
                  <MetaRow icon={Calendar} label="Added" value={formatDate(mod.created_at)} />
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Recent Audit Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <Boxes className="h-8 w-8 text-muted-foreground/40 mb-3" />
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

        {/* Placeholder tabs */}
        <TabsContent value="assessments" className="pt-4">
          <PlaceholderTab label="Assessment management" />
        </TabsContent>
        <TabsContent value="moderation" className="pt-4">
          <PlaceholderTab label="Moderation evidence" />
        </TabsContent>
        <TabsContent value="evidence" className="pt-4">
          <PlaceholderTab label="Evidence upload and tracking" />
        </TabsContent>
        <TabsContent value="audits" className="pt-4">
          <PlaceholderTab label="Audit runs and reports" />
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings" className="pt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Module Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                {[
                  ["Module ID", mod.id],
                  ["Programme ID", mod.programme_id],
                  ["Lecturer ID", mod.lecturer_id ?? "Not assigned"],
                  ["Created", formatDateTime(mod.created_at)],
                  ["Last updated", formatDateTime(mod.updated_at)],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between py-2 border-b">
                    <span>{label}</span>
                    <span className="font-mono text-xs text-foreground truncate max-w-[220px]">
                      {val}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <Link
                  href={`/modules/${id}/edit`}
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                >
                  <Pencil className="mr-1.5 h-3.5 w-3.5" />
                  Edit Module
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
