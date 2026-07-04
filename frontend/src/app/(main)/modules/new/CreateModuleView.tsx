"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Boxes } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { ModuleForm } from "@/components/modules/ModuleForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateModule } from "@/hooks/useModules";
import { useAuthStore } from "@/store/auth.store";
import { useRole } from "@/hooks/useRole";
import type { ModuleFormValues } from "@/components/modules/ModuleForm";

export function CreateModuleView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isSysAdmin } = useRole();
  const user = useAuthStore((s) => s.user);
  const createMutation = useCreateModule();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>();

  const defaultProgrammeId = searchParams.get("programme_id") ?? undefined;
  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: ModuleFormValues) {
    setServerErrors(undefined);
    try {
      const mod = await createMutation.mutateAsync({
        programme_id: values.programme_id,
        name: values.name,
        code: values.code,
        credits: parseInt(values.credits, 10),
        semester: values.semester,
        academic_year: values.academic_year,
      });
      toast.success("Module created", { description: `${mod.name} has been added.` });
      router.push(`/modules/${mod.id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This module code already exists in this programme for the same academic year.",
        });
      }
    }
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
            You don&apos;t have permission to create modules.
          </p>
        </div>
      }
    >
      <PageHeader
        title="New Module"
        subtitle="Create a module within a programme."
        actions={
          <Link
            href="/modules"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            Cancel
          </Link>
        }
      />
      <div className="max-w-2xl">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-6 pb-6 border-b">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Boxes className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Module details</p>
                <p className="text-xs text-muted-foreground">
                  Select the programme, then fill in the module details.
                </p>
              </div>
            </div>
            <ModuleForm
              lockedInstitutionId={lockedInstitutionId}
              defaultProgrammeId={defaultProgrammeId}
              onSubmit={handleSubmit}
              onCancel={() => router.push("/modules")}
              isPending={createMutation.isPending}
              serverErrors={serverErrors}
              submitLabel="Create Module"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
