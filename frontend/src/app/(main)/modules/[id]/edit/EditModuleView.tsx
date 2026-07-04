"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { ModuleForm } from "@/components/modules/ModuleForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useModule, useUpdateModule, useDeleteModule } from "@/hooks/useModules";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import type { ModuleFormValues } from "@/components/modules/ModuleForm";

function EditSkeleton() {
  return (
    <div className="max-w-2xl space-y-4">
      <Skeleton className="h-8 w-48" />
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function EditModuleView({ id }: { id: string }) {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer, isCoordinator } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: mod, isLoading, isError, refetch } = useModule(id);
  const updateMutation = useUpdateModule(id);
  const deleteMutation = useDeleteModule();

  const [serverErrors, setServerErrors] = useState<Record<string, string>>();
  const [showDelete, setShowDelete] = useState(false);

  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;
  const canDelete = isSysAdmin || isQAOfficer || isCoordinator;

  async function handleSubmit(values: ModuleFormValues) {
    setServerErrors(undefined);
    if (!mod) return;
    try {
      const payload: Record<string, unknown> = {};
      if (values.name !== mod.name) payload.name = values.name;
      if (values.code !== mod.code) payload.code = values.code;
      const credits = parseInt(values.credits, 10);
      if (credits !== mod.credits) payload.credits = credits;
      if (values.semester !== mod.semester) payload.semester = values.semester;
      if (values.academic_year !== mod.academic_year)
        payload.academic_year = values.academic_year;

      await updateMutation.mutateAsync(payload);
      router.push(`/modules/${id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This module code already exists in this programme for the same academic year.",
        });
      }
    }
  }

  async function handleDelete() {
    if (!mod) return;
    await deleteMutation.mutateAsync(id);
    setShowDelete(false);
    toast.success(`${mod.name} has been deleted.`);
    router.push("/modules");
  }

  if (isLoading) return <EditSkeleton />;
  if (isError || !mod) {
    return (
      <ErrorState
        title="Module not found"
        message="This module doesn't exist or you don't have access."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <RoleGuard
      roles={[
        "system_admin",
        "quality_assurance_officer",
        "faculty_dean",
        "head_of_department",
        "programme_coordinator",
      ]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            You don&apos;t have permission to edit modules.
          </p>
        </div>
      }
    >
      <PageHeader
        title={`Edit — ${mod.name}`}
        subtitle="Update module metadata."
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/modules/${id}`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Cancel
            </Link>
            {canDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDelete(true)}
              >
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Delete
              </Button>
            )}
          </div>
        }
      />

      <div className="max-w-2xl">
        <Card>
          <CardContent className="pt-6">
            <ModuleForm
              defaultValues={mod}
              lockedInstitutionId={lockedInstitutionId}
              onSubmit={handleSubmit}
              onCancel={() => router.push(`/modules/${id}`)}
              isPending={updateMutation.isPending}
              isEdit
              serverErrors={serverErrors}
              submitLabel="Save Changes"
            />
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={showDelete}
        onOpenChange={setShowDelete}
        title="Delete Module"
        description={`Are you sure you want to permanently delete "${mod.name}"? This will remove all evidence files and audit history. This cannot be undone.`}
        confirmLabel="Delete Module"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </RoleGuard>
  );
}
