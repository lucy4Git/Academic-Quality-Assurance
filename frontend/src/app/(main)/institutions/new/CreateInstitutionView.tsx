"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Building2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { InstitutionForm } from "@/components/institutions/InstitutionForm";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateInstitution } from "@/hooks/useInstitutions";
import type { InstitutionFormValues } from "@/components/institutions/InstitutionForm";

export function CreateInstitutionView() {
  const router = useRouter();
  const createMutation = useCreateInstitution();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>();

  async function handleSubmit(values: InstitutionFormValues) {
    setServerErrors(undefined);
    try {
      const institution = await createMutation.mutateAsync({
        name: values.name,
        code: values.code,
        country: values.country || null,
        address: values.address || null,
        logo_url: values.logo_url || null,
      });
      toast.success("Institution created", {
        description: `${institution.name} has been registered.`,
      });
      router.push(`/institutions/${institution.id}`);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerErrors({
          code: "This institution code is already in use.",
        });
      }
    }
  }

  return (
    <RoleGuard
      roles={["system_admin"]}
      fallback={
        <div className="py-16 text-center">
          <p className="text-muted-foreground">
            Only System Administrators can create institutions.
          </p>
        </div>
      }
    >
      <PageHeader
        title="New Institution"
        subtitle="Register a new institution on the AQAA platform."
        actions={
          <Link
            href="/institutions"
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
                <Building2 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Institution details</p>
                <p className="text-xs text-muted-foreground">
                  All seeded users share password ChangeMe123! for local dev.
                </p>
              </div>
            </div>
            <InstitutionForm
              onSubmit={handleSubmit}
              onCancel={() => router.push("/institutions")}
              isPending={createMutation.isPending}
              serverErrors={serverErrors}
              submitLabel="Create Institution"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
