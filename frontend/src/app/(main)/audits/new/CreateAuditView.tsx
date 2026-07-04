"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { SearchCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { PageHeader } from "@/components/common/PageHeader";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useCreateAudit } from "@/hooks/useModuleAudits";
import { useModules } from "@/hooks/useModules";
import { useAuthStore } from "@/store/auth.store";
import { useRole } from "@/hooks/useRole";

export function CreateAuditView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isSysAdmin } = useRole();
  const user = useAuthStore((s) => s.user);
  const { data: modules } = useModules();
  const createMutation = useCreateAudit();

  const [moduleId, setModuleId] = useState(searchParams.get("module_id") ?? "");
  const [academicYear, setAcademicYear] = useState("2025/2026");
  const [notes, setNotes] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Scope modules to user's institution for non-SA
  const scopedModules = isSysAdmin
    ? modules
    : modules?.filter((m) => {
        // All modules visible to user (server already scoped)
        return true;
      });

  function validate() {
    const e: Record<string, string> = {};
    if (!moduleId) e.module_id = "Module is required.";
    if (!academicYear.match(/^\d{4}\/\d{4}$/)) e.academic_year = "Format: YYYY/YYYY";
    else {
      const [s, en] = academicYear.split("/").map(Number);
      if (en !== s + 1) e.academic_year = "End year must be start year + 1.";
    }
    return e;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    try {
      const audit = await createMutation.mutateAsync({ module_id: moduleId, academic_year: academicYear, notes: notes || null });
      toast.success("Audit created", { description: "Complete the checklist to assess compliance." });
      router.push(`/audits/${audit.id}`);
    } catch (err) {
      if (axios.isAxiosError(err)) toast.error("Failed to create audit", { description: err.response?.data?.detail });
    }
  }

  return (
    <RoleGuard
      roles={["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"]}
      fallback={<div className="py-16 text-center"><p className="text-muted-foreground">You don&apos;t have permission to create audits.</p></div>}
    >
      <PageHeader
        title="New Module Folder Audit"
        subtitle="Select a module and academic year to begin a quality assurance audit."
        actions={<Link href="/audits" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>Cancel</Link>}
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-6 pb-6 border-b">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <SearchCheck className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Audit details</p>
                <p className="text-xs text-muted-foreground">A checklist of 10 QA criteria will be generated automatically.</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              <div className="space-y-1.5">
                <Label htmlFor="a-module">Module <span className="text-destructive">*</span></Label>
                <select
                  id="a-module"
                  value={moduleId}
                  onChange={(e) => setModuleId(e.target.value)}
                  className={cn(
                    "flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm",
                    errors.module_id ? "border-destructive" : "border-input"
                  )}
                >
                  <option value="">Select a module…</option>
                  {scopedModules?.map((m) => (
                    <option key={m.id} value={m.id}>{m.code} — {m.name} ({m.academic_year})</option>
                  ))}
                </select>
                {errors.module_id && <p role="alert" className="text-xs text-destructive">{errors.module_id}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="a-year">Academic Year <span className="text-destructive">*</span></Label>
                <Input
                  id="a-year"
                  placeholder="2025/2026"
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className={errors.academic_year ? "border-destructive" : ""}
                />
                {errors.academic_year && <p role="alert" className="text-xs text-destructive">{errors.academic_year}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="a-notes">Notes (optional)</Label>
                <textarea
                  id="a-notes"
                  rows={3}
                  placeholder="Any preliminary observations or context…"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t">
                <Button type="button" variant="outline" onClick={() => router.push("/audits")} disabled={createMutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Audit
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
