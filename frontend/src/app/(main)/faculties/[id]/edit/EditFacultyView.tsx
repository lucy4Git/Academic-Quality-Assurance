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
import { FacultyForm } from "@/components/faculties/FacultyForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  useFaculty,
  useUpdateFaculty,
  useDeleteFaculty,
} from "@/hooks/useFaculties";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import type { FacultyFormValues } from "@/components/faculties/FacultyForm";

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

export function EditFacultyView({ id }: Props) {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: faculty, isLoading, isError, refetch } = useFaculty(id);
  const { data: institutions } = useInstitutions();
  const updateMutation = useUpdateFaculty(id);
  const deleteMutation = useDeleteFaculty();

  const [serverErrors, setServerErrors] = useState<Record<string, string>>();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // QA Officer is locked to their institution; SA can pick any
  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: FacultyFormValues) {
    setServerErrors(undefined);
    if (!faculty) return;

    try {
      // Send only changed fields
      const payload: Record<string, string | null> = {};
      if (values.name !== faculty.name) payload.name = values.name;
      if (values.code !== faculty.code) payload.code = values.code;
      const newCampus = values.campus || null;
      if (newCampus !== faculty.campus) payload.campus = newCampus;

      await updateMutation.mutateAsync(payload);
      router.push(`/faculties/${id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This faculty code is already in use within this institution.",
        });
      }
    }
  }

  async function handleDelete() {
    if (!faculty) return;
    await deleteMutation.mutateAsync(id);
    setShowDeleteDialog(false);
    toast.success(`${faculty.name} has been deleted.`);
    router.push("/faculties");
  }

  if (isLoading) return <EditSkeleton />;

  if (isError || !faculty) {
    return (
      <ErrorState
        title="Faculty not found"
        message="This faculty doesn't exist or you don't have access."
        onRetry={() => refetch()}
      />
    );
  }

  const canDelete = isSysAdmin || isQAOfficer;

  return (
    <RoleGuard
      roles={[
        "system_admin",
        "quality_assurance_officer",
        "faculty_dean",
      ]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only QA Officers, Faculty Deans, and System Administrators can edit
            faculties.
          </p>
        </div>
      }
    >
      <PageHeader
        title={`Edit — ${faculty.name}`}
        subtitle="Update faculty metadata."
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/faculties/${id}`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Cancel
            </Link>
            {canDelete && (
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
            <FacultyForm
              defaultValues={faculty}
              institutions={institutions}
              lockedInstitutionId={lockedInstitutionId ?? faculty.institution_id}
              onSubmit={handleSubmit}
              onCancel={() => router.push(`/faculties/${id}`)}
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
        title="Delete Faculty"
        description={`Are you sure you want to permanently delete "${faculty.name}"? This will remove all departments, programmes, modules, files, and audit history under this faculty. This cannot be undone.`}
        confirmLabel="Delete Faculty"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </RoleGuard>
  );
}
