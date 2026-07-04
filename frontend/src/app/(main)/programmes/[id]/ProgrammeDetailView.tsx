"use client";

import Link from "next/link";
import { Layers, Pencil, Calendar, BookOpen } from "lucide-react";

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
import { useProgramme } from "@/hooks/useProgrammes";
import { useDepartment } from "@/hooks/useDepartments";
import { PROGRAMME_LEVEL_LABELS } from "@/types";

const LEVEL_BADGE: Record<string, string> = {
  undergraduate: "text-blue-700 bg-blue-50 border-blue-200",
  postgraduate:  "text-purple-700 bg-purple-50 border-purple-200",
  doctoral:      "text-amber-700 bg-amber-50 border-amber-200",
};

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2"><Skeleton className="h-8 w-56" /><Skeleton className="h-4 w-40" /></div>
        <Skeleton className="h-8 w-16" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">{Array.from({length:3}).map((_,i)=><Skeleton key={i} className="h-20 rounded-xl"/>)}</div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

function MetaRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string | null | undefined }) {
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

export function ProgrammeDetailView({ id }: { id: string }) {
  const { data: prog, isLoading, isError, refetch } = useProgramme(id);
  const { data: dept } = useDepartment(prog?.department_id ?? "");

  if (isLoading) return <DetailSkeleton />;
  if (isError || !prog) return (
    <ErrorState title="Programme not found" message="This programme does not exist or you don't have access." onRetry={() => refetch()} />
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={prog.name}
        subtitle={`${prog.code} · ${dept?.name ?? "—"}`}
        actions={
          <RoleGuard roles={["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"]}>
            <Link href={`/programmes/${id}/edit`} className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit
            </Link>
          </RoleGuard>
        }
      />

      {/* Level badge */}
      <div className="-mt-4">
        <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", LEVEL_BADGE[prog.level] ?? "text-slate-600 bg-slate-50 border-slate-200")}>
          {PROGRAMME_LEVEL_LABELS[prog.level]}
        </span>
      </div>

      <Tabs defaultValue="overview">
        <TabsList variant="line">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <RoleGuard roles={["system_admin","quality_assurance_officer","faculty_dean","head_of_department","programme_coordinator"]}>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </RoleGuard>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="pt-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Programme Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Layers className="h-7 w-7 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-foreground truncate">{prog.name}</p>
                    <Badge variant="secondary" className="font-mono text-xs mt-1">{prog.code}</Badge>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  <MetaRow icon={BookOpen} label="Department" value={dept?.name} />
                  <MetaRow icon={Layers} label="Level" value={PROGRAMME_LEVEL_LABELS[prog.level]} />
                  {prog.qualification_type && (
                    <MetaRow icon={Layers} label="Qualification Type" value={prog.qualification_type} />
                  )}
                  {prog.nqf_level != null && (
                    <MetaRow icon={Layers} label="NQF Level" value={`Level ${prog.nqf_level}`} />
                  )}
                  {prog.duration_years != null && (
                    <MetaRow icon={Calendar} label="Duration" value={`${prog.duration_years} year${prog.duration_years !== 1 ? "s" : ""}`} />
                  )}
                  {prog.total_credits != null && (
                    <MetaRow icon={Layers} label="Total Credits" value={prog.total_credits.toString()} />
                  )}
                  {prog.status && (
                    <MetaRow icon={Layers} label="Status" value={prog.status.replace(/_/g, " ")} />
                  )}
                  <MetaRow icon={Calendar} label="Added" value={formatDate(prog.created_at)} />
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <Layers className="h-8 w-8 text-muted-foreground/40 mb-3" />
                  <p className="text-sm text-muted-foreground">Module and audit activity will appear here.</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">Available in Phase 2 Module Management.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Modules — placeholder */}
        <TabsContent value="modules" className="pt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <Layers className="h-8 w-8 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">Module management is implemented in Phase 2.</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings" className="pt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Programme Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                {[
                  ["Programme ID", prog.id],
                  ["Department ID", prog.department_id],
                  ["Created", formatDateTime(prog.created_at)],
                  ["Last updated", formatDateTime(prog.updated_at)],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between py-2 border-b">
                    <span>{label}</span>
                    <span className="font-mono text-xs text-foreground truncate max-w-[200px]">{val}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <Link href={`/programmes/${id}/edit`} className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
                  <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit Programme
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
