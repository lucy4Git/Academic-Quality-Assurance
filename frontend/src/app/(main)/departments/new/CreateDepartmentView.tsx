"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { BookOpen } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { DepartmentForm } from "@/components/departments/DepartmentForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateDepartment } from "@/hooks/useDepartments";
import { useAuthStore } from "@/store/auth.store";
import { useRole } from "@/hooks/useRole";
import type { DepartmentFormValues } from "@/components/departments/DepartmentForm";

export function CreateDepartmentView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isSysAdmin } = useRole();
  const user = useAuthStore((s) => s.user);
  const createMutation = useCreateDepartment();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>();

  // Support pre-filling faculty from query param (e.g. from faculty detail page)
  const defaultFacultyId = searchParams.get("faculty_id") ?? undefined;

  const lockedInstitutionId =
    !isSysAdmin && user?.institution_id ? user.institution_id : undefined;

  async function handleSubmit(values: DepartmentFormValues) {
    setServerErrors(undefined);
    try {
      const dept = await createMutation.mutateAsync({
        faculty_id: values.faculty_id,
        name: values.name,
        code: values.code,
      });
      toast.success("Department created", {
        description: `${dept.name} has been added.`,
      });
      router.push(`/departments/${dept.id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This department code is already in use within the selected faculty.",
        });
      }
    }
  }

  return (
    <RoleGuard
      roles={["system_admin", "quality_assurance_officer", "faculty_dean"]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only Faculty Deans, QA Officers, and System Administrators can
            create departments.
          </p>
        </div>
      }
    >
      <PageHeader
        title="New Department"
        subtitle="Create a department within a faculty."
        actions={
          <Link
            href="/departments"
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
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Department details</p>
                <p className="text-xs text-muted-foreground">
                  {isSysAdmin
                    ? "Select an institution, then a faculty, and fill in the department details."
                    : "Select a faculty and fill in the department details."}
                </p>
              </div>
            </div>

            <DepartmentForm
              lockedInstitutionId={lockedInstitutionId}
              defaultFacultyId={defaultFacultyId}
              onSubmit={handleSubmit}
              onCancel={() => router.push("/departments")}
              isPending={createMutation.isPending}
              serverErrors={serverErrors}
              submitLabel="Create Department"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
