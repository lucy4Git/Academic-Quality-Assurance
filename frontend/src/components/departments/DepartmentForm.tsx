"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFaculties } from "@/hooks/useFaculties";
import { useInstitutions } from "@/hooks/useInstitutions";
import type { Department } from "@/types";

const departmentSchema = z.object({
  institution_id: z.string().optional(),
  faculty_id: z
    .string()
    .min(1, "Faculty is required.")
    .uuid("Must be a valid faculty."),
  name: z
    .string()
    .min(2, "Department name must be at least 2 characters.")
    .max(255, "Department name must be 255 characters or fewer."),
  code: z
    .string()
    .min(2, "Code must be at least 2 characters.")
    .max(20, "Code must be 20 characters or fewer.")
    .regex(
      /^[A-Z0-9][A-Z0-9\-_]{1,19}$/,
      "Code must be uppercase letters, digits, hyphens, or underscores only."
    ),
});

export type DepartmentFormValues = z.infer<typeof departmentSchema>;

interface DepartmentFormProps {
  defaultValues?: Partial<Department>;
  /** Locked institution when user is non-SA (QA, Dean, HOD) */
  lockedInstitutionId?: string;
  /** Pre-selected faculty_id (e.g. when coming from a faculty detail page) */
  defaultFacultyId?: string;
  onSubmit: (values: DepartmentFormValues) => void | Promise<void>;
  onCancel: () => void;
  isPending?: boolean;
  isEdit?: boolean;
  serverErrors?: Record<string, string>;
  submitLabel?: string;
}

export function DepartmentForm({
  defaultValues,
  lockedInstitutionId,
  defaultFacultyId,
  onSubmit,
  onCancel,
  isPending = false,
  isEdit = false,
  serverErrors,
  submitLabel = "Save",
}: DepartmentFormProps) {
  const { data: institutions } = useInstitutions();

  // Institution selection state (SA only)
  const [selectedInstitutionId, setSelectedInstitutionId] = useState<string>(
    lockedInstitutionId ??
      defaultValues?.faculty_id
        ? "" // will be resolved after faculties load
        : ""
  );

  const effectiveInstitutionId = lockedInstitutionId ?? selectedInstitutionId;

  // Load faculties filtered by selected institution
  const { data: allFaculties } = useFaculties(
    effectiveInstitutionId || undefined
  );

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    watch,
    formState: { errors },
  } = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentSchema),
    defaultValues: {
      institution_id: lockedInstitutionId ?? "",
      faculty_id: defaultValues?.faculty_id ?? defaultFacultyId ?? "",
      name: defaultValues?.name ?? "",
      code: defaultValues?.code ?? "",
    },
  });

  const watchedFacultyId = watch("faculty_id");

  // When editing: resolve the institution from the existing faculty_id
  useEffect(() => {
    if (!isEdit || !defaultValues?.faculty_id || !allFaculties) return;
    const fac = allFaculties.find((f) => f.id === defaultValues.faculty_id);
    if (fac && !lockedInstitutionId) {
      setSelectedInstitutionId(fac.institution_id);
    }
  }, [isEdit, defaultValues?.faculty_id, allFaculties, lockedInstitutionId]);

  // Also try to resolve institution_id from all-institutions fetch on edit
  useEffect(() => {
    if (!isEdit || !defaultValues?.faculty_id) return;
    // If we have faculties loaded (no institution filter yet), find the faculty
    if (allFaculties) {
      const fac = allFaculties.find((f) => f.id === defaultValues.faculty_id);
      if (fac) setSelectedInstitutionId(fac.institution_id);
    }
  }, [allFaculties, defaultValues?.faculty_id, isEdit]);

  // Propagate server errors
  useEffect(() => {
    if (!serverErrors) return;
    Object.entries(serverErrors).forEach(([field, message]) => {
      setError(field as keyof DepartmentFormValues, { type: "server", message });
    });
  }, [serverErrors, setError]);

  function handleCodeBlur(e: React.FocusEvent<HTMLInputElement>) {
    setValue("code", e.target.value.toUpperCase().trim(), {
      shouldValidate: true,
    });
  }

  function handleInstitutionChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedInstitutionId(e.target.value);
    setValue("faculty_id", ""); // reset faculty when institution changes
  }

  const showInstitutionSelect = !lockedInstitutionId;
  const institutionForDisplay = lockedInstitutionId
    ? institutions?.find((i) => i.id === lockedInstitutionId)?.name
    : undefined;

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {/* Institution — SA sees select; QA/Dean sees locked label */}
      {showInstitutionSelect ? (
        <div className="space-y-1.5">
          <Label htmlFor="institution_id">Institution</Label>
          <select
            id="institution_id"
            value={selectedInstitutionId}
            onChange={handleInstitutionChange}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Select an institution…</option>
            {institutions?.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name} ({inst.code})
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="space-y-1.5">
          <Label>Institution</Label>
          <p className="text-sm text-foreground rounded-md border border-input bg-muted px-3 py-2">
            {institutionForDisplay ?? "Your institution"}
          </p>
        </div>
      )}

      {/* Faculty selector — filtered by institution */}
      <div className="space-y-1.5">
        <Label htmlFor="faculty_id">
          Faculty <span className="text-destructive">*</span>
        </Label>
        <select
          id="faculty_id"
          aria-invalid={!!errors.faculty_id}
          aria-describedby={errors.faculty_id ? "faculty-error" : undefined}
          disabled={!effectiveInstitutionId && !isEdit}
          className={`flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed ${
            errors.faculty_id ? "border-destructive" : "border-input"
          }`}
          {...register("faculty_id")}
        >
          <option value="">
            {effectiveInstitutionId || isEdit
              ? "Select a faculty…"
              : "Select an institution first…"}
          </option>
          {allFaculties?.map((fac) => (
            <option key={fac.id} value={fac.id}>
              {fac.name} ({fac.code}){fac.campus ? ` — ${fac.campus}` : ""}
            </option>
          ))}
        </select>
        {errors.faculty_id && (
          <p id="faculty-error" role="alert" className="text-xs text-destructive">
            {errors.faculty_id.message}
          </p>
        )}
      </div>

      {/* Department Name */}
      <div className="space-y-1.5">
        <Label htmlFor="name">
          Department Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder="e.g. Department of Computer Science"
          autoFocus={isEdit}
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? "name-error" : undefined}
          {...register("name")}
          className={errors.name ? "border-destructive" : ""}
        />
        {errors.name && (
          <p id="name-error" role="alert" className="text-xs text-destructive">
            {errors.name.message}
          </p>
        )}
      </div>

      {/* Department Code */}
      <div className="space-y-1.5">
        <Label htmlFor="code">
          Department Code <span className="text-destructive">*</span>
        </Label>
        <Input
          id="code"
          placeholder="e.g. CS"
          className={`font-mono uppercase ${errors.code ? "border-destructive" : ""}`}
          aria-invalid={!!errors.code}
          aria-describedby={errors.code ? "code-error" : "code-hint"}
          {...register("code")}
          onBlur={handleCodeBlur}
        />
        {errors.code ? (
          <p id="code-error" role="alert" className="text-xs text-destructive">
            {errors.code.message}
          </p>
        ) : (
          <p id="code-hint" className="text-xs text-muted-foreground">
            2–20 uppercase letters, digits, hyphens, or underscores.
          </p>
        )}
      </div>

      {/* head_id — deferred to Phase 3 (no user-listing endpoint) */}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-2 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isPending}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
