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
import { DepartmentForm } from "@/components/departments/DepartmentForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  useDepartment,
  useUpdateDepartment,
  useDeleteDepartment,
} from "@/hooks/useDepartments";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import type { DepartmentFormValues } from "@/components/departments/DepartmentForm";

interface Props {
  id: string;
}

function EditSkeleton() {
  return (
    <div className="max-w-lg space-y-4">
      <Skeleton className="h-8 w-48" />
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

export function EditDepartmentView({ id }: Props) {
  const router = useRouter();
  const { isSysAdmin, isHOD } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: dept, isLoading, isError, refetch } = useDepartment(id);
  const updateMutation = useUpdateDepartment(id);
  const deleteMutation = useDeleteDepartment();

  const [serverErrors, setServerErrors] = useState<Record<string, string>>();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Non-SA are locked to their institution
  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: DepartmentFormValues) {
    setServerErrors(undefined);
    if (!dept) return;
    try {
      const payload: Record<string, string | null> = {};
      if (values.name !== dept.name) payload.name = values.name;
      if (values.code !== dept.code) payload.code = values.code;
      await updateMutation.mutateAsync(payload);
      router.push(`/departments/${id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This department code is already in use within this faculty.",
        });
      }
    }
  }

  async function handleDelete() {
    if (!dept) return;
    await deleteMutation.mutateAsync(id);
    setShowDeleteDialog(false);
    toast.success(`${dept.name} has been deleted.`);
    router.push("/departments");
  }

  if (isLoading) return <EditSkeleton />;

  if (isError || !dept) {
    return (
      <ErrorState
        title="Department not found"
        message="This department doesn't exist or you don't have access."
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
      ]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only Heads of Department, Faculty Deans, QA Officers, and System
            Administrators can edit departments.
          </p>
        </div>
      }
    >
      <PageHeader
        title={`Edit — ${dept.name}`}
        subtitle="Update department metadata."
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/departments/${id}`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Cancel
            </Link>
            {isHOD && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Delete
              </Button>
            )}
          </div>
        }
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <DepartmentForm
              defaultValues={dept}
              lockedInstitutionId={lockedInstitutionId}
              onSubmit={handleSubmit}
              onCancel={() => router.push(`/departments/${id}`)}
              isPending={updateMutation.isPending}
              isEdit
              serverErrors={serverErrors}
              submitLabel="Save Changes"
            />
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete Department"
        description={`Are you sure you want to permanently delete "${dept.name}"? This will remove all programmes, modules, files, and audit history under this department. This cannot be undone.`}
        confirmLabel="Delete Department"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </RoleGuard>
  );
}
