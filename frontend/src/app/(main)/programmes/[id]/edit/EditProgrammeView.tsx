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
import { ProgrammeForm } from "@/components/programmes/ProgrammeForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useProgramme, useUpdateProgramme, useDeleteProgramme } from "@/hooks/useProgrammes";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import type { ProgrammeFormValues } from "@/components/programmes/ProgrammeForm";

function EditSkeleton() {
  return (
    <div className="max-w-lg space-y-4">
      <Skeleton className="h-8 w-48" />
      {Array.from({length:5}).map((_,i)=><Skeleton key={i} className="h-10 w-full"/>)}
    </div>
  );
}

export function EditProgrammeView({ id }: { id: string }) {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: prog, isLoading, isError, refetch } = useProgramme(id);
  const updateMutation = useUpdateProgramme(id);
  const deleteMutation = useDeleteProgramme();

  const [serverErrors, setServerErrors] = useState<Record<string, string>>();
  const [showDelete, setShowDelete] = useState(false);

  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: ProgrammeFormValues) {
    setServerErrors(undefined);
    if (!prog) return;
    try {
      const payload: Record<string, unknown> = {};
      if (values.name !== prog.name) payload.name = values.name;
      if (values.code !== prog.code) payload.code = values.code;
      if (values.level !== prog.level) payload.level = values.level;
      // Extended QA fields — always include so they can be cleared
      payload.qualification_type = values.qualification_type || null;
      payload.nqf_level = values.nqf_level ? parseInt(values.nqf_level, 10) : null;
      payload.duration_years = values.duration_years ? parseInt(values.duration_years, 10) : null;
      payload.total_credits = values.total_credits ? parseInt(values.total_credits, 10) : null;
      payload.status = values.status || "active";
      await updateMutation.mutateAsync(payload);
      router.push(`/programmes/${id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({ code: "This programme code is already in use within this department." });
      }
    }
  }

  async function handleDelete() {
    if (!prog) return;
    await deleteMutation.mutateAsync(id);
    setShowDelete(false);
    toast.success(`${prog.name} has been deleted.`);
    router.push("/programmes");
  }

  if (isLoading) return <EditSkeleton />;
  if (isError || !prog) return (
    <ErrorState title="Programme not found" message="This programme doesn't exist or you don't have access." onRetry={() => refetch()} />
  );

  const canDelete = isSysAdmin || isQAOfficer;

  return (
    <RoleGuard
      roles={["system_admin","quality_assurance_officer","faculty_dean","head_of_department","programme_coordinator"]}
      fallback={<div className="py-16 text-center"><p className="text-muted-foreground">You don&apos;t have permission to edit programmes.</p></div>}
    >
      <PageHeader
        title={`Edit — ${prog.name}`}
        subtitle="Update programme metadata."
        actions={
          <div className="flex items-center gap-2">
            <Link href={`/programmes/${id}`} className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              Cancel
            </Link>
            {canDelete && (
              <Button variant="destructive" size="sm" onClick={() => setShowDelete(true)}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Delete
              </Button>
            )}
          </div>
        }
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <ProgrammeForm
              defaultValues={prog}
              lockedInstitutionId={lockedInstitutionId}
              onSubmit={handleSubmit}
              onCancel={() => router.push(`/programmes/${id}`)}
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
        title="Delete Programme"
        description={`Are you sure you want to permanently delete "${prog.name}"? This will remove all modules and audit history. This cannot be undone.`}
        confirmLabel="Delete Programme"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </RoleGuard>
  );
}
