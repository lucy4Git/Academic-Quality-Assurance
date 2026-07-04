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
import { InstitutionForm } from "@/components/institutions/InstitutionForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  useInstitution,
  useUpdateInstitution,
  useDeleteInstitution,
} from "@/hooks/useInstitutions";
import type { InstitutionFormValues } from "@/components/institutions/InstitutionForm";

interface Props {
  id: string;
}

function EditSkeleton() {
  return (
    <div className="max-w-lg space-y-4">
      <Skeleton className="h-8 w-56" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

export function EditInstitutionView({ id }: Props) {
  const router = useRouter();
  const { data: institution, isLoading, isError, refetch } = useInstitution(id);
  const updateMutation = useUpdateInstitution(id);
  const deleteMutation = useDeleteInstitution();

  const [serverErrors, setServerErrors] = useState<Record<string, string>>();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  async function handleSubmit(values: InstitutionFormValues) {
    setServerErrors(undefined);
    try {
      // Only send fields that changed
      const payload: Record<string, string | null> = {};
      if (values.name !== institution?.name) payload.name = values.name;
      if (values.code !== institution?.code) payload.code = values.code;
      if ((values.country || null) !== institution?.country)
        payload.country = values.country || null;
      if ((values.address || null) !== institution?.address)
        payload.address = values.address || null;
      if ((values.logo_url || null) !== institution?.logo_url)
        payload.logo_url = values.logo_url || null;

      await updateMutation.mutateAsync(payload);
      router.push(`/institutions/${id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({ code: "This institution code is already in use." });
      }
    }
  }

  async function handleDelete() {
    await deleteMutation.mutateAsync(id);
    setShowDeleteDialog(false);
    toast.success(`${institution?.name} has been deleted.`);
    router.push("/institutions");
  }

  if (isLoading) return <EditSkeleton />;

  if (isError || !institution) {
    return (
      <ErrorState
        title="Institution not found"
        message="This institution doesn't exist or you don't have access."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <RoleGuard
      roles={["system_admin"]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only System Administrators can edit institutions.
          </p>
        </div>
      }
    >
      <PageHeader
        title={`Edit — ${institution.name}`}
        subtitle="Update institution metadata."
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/institutions/${id}`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              Cancel
            </Link>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              Delete
            </Button>
          </div>
        }
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <InstitutionForm
              defaultValues={institution}
              onSubmit={handleSubmit}
              onCancel={() => router.push(`/institutions/${id}`)}
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
        title="Delete Institution"
        description={`Are you sure you want to permanently delete "${institution.name}"? This will remove all faculties, departments, programmes, modules, files, and audit history. This cannot be undone.`}
        confirmLabel="Delete Institution"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </RoleGuard>
  );
}
