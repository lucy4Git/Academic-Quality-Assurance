"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Layers } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { ProgrammeForm } from "@/components/programmes/ProgrammeForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateProgramme } from "@/hooks/useProgrammes";
import { useAuthStore } from "@/store/auth.store";
import { useRole } from "@/hooks/useRole";
import type { ProgrammeFormValues } from "@/components/programmes/ProgrammeForm";

export function CreateProgrammeView() {
  const router = useRouter();
  const { isSysAdmin } = useRole();
  const user = useAuthStore((s) => s.user);
  const createMutation = useCreateProgramme();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>();

  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: ProgrammeFormValues) {
    setServerErrors(undefined);
    try {
      const prog = await createMutation.mutateAsync({
        department_id: values.department_id,
        name: values.name,
        code: values.code,
        level: values.level,
        qualification_type: values.qualification_type || null,
        nqf_level: values.nqf_level ? parseInt(values.nqf_level, 10) : null,
        duration_years: values.duration_years ? parseInt(values.duration_years, 10) : null,
        total_credits: values.total_credits ? parseInt(values.total_credits, 10) : null,
        status: values.status || "active",
      });
      toast.success("Programme created", { description: `${prog.name} has been added.` });
      router.push(`/programmes/${prog.id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({ code: "This programme code is already in use within the selected department." });
      }
    }
  }

  return (
    <RoleGuard
      roles={["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department"]}
      fallback={<div className="py-16 text-center"><p className="text-muted-foreground">You don&apos;t have permission to create programmes.</p></div>}
    >
      <PageHeader
        title="New Programme"
        subtitle="Create a programme within a department."
        actions={
          <Link href="/programmes" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            Cancel
          </Link>
        }
      />
      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-6 pb-6 border-b">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Layers className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Programme details</p>
                <p className="text-xs text-muted-foreground">
                  Select an institution, faculty, and department, then fill in the programme details.
                </p>
              </div>
            </div>
            <ProgrammeForm
              lockedInstitutionId={lockedInstitutionId}
              onSubmit={handleSubmit}
              onCancel={() => router.push("/programmes")}
              isPending={createMutation.isPending}
              serverErrors={serverErrors}
              submitLabel="Create Programme"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
