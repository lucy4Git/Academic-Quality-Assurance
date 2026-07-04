"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GraduationCap } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { FacultyForm } from "@/components/faculties/FacultyForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateFaculty } from "@/hooks/useFaculties";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useAuthStore } from "@/store/auth.store";
import { useRole } from "@/hooks/useRole";
import type { FacultyFormValues } from "@/components/faculties/FacultyForm";

export function CreateFacultyView() {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: institutions } = useInstitutions();
  const createMutation = useCreateFaculty();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>();

  // QA Officer's institution is locked; SA picks from the list
  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: FacultyFormValues) {
    setServerErrors(undefined);
    try {
      const faculty = await createMutation.mutateAsync({
        institution_id: values.institution_id,
        name: values.name,
        code: values.code,
        campus: values.campus || null,
      });
      toast.success("Faculty created", {
        description: `${faculty.name} has been added.`,
      });
      router.push(`/faculties/${faculty.id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This faculty code is already in use within the selected institution.",
        });
      }
    }
  }

  return (
    <RoleGuard
      roles={["system_admin", "quality_assurance_officer"]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only QA Officers and System Administrators can create faculties.
          </p>
        </div>
      }
    >
      <PageHeader
        title="New Faculty"
        subtitle="Create a faculty within an institution."
        actions={
          <Link
            href="/faculties"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            Cancel
          </Link>
        }
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-6 pb-6 border-b">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <GraduationCap className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Faculty details</p>
                <p className="text-xs text-muted-foreground">
                  {isSysAdmin
                    ? "Select an institution and fill in the faculty details."
                    : "Faculty will be created under your institution."}
                </p>
              </div>
            </div>

            <FacultyForm
              institutions={institutions}
              lockedInstitutionId={lockedInstitutionId}
              onSubmit={handleSubmit}
              onCancel={() => router.push("/faculties")}
              isPending={createMutation.isPending}
              serverErrors={serverErrors}
              submitLabel="Create Faculty"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
