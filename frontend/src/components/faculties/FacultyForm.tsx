"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Faculty, Institution } from "@/types";

const facultySchema = z.object({
  institution_id: z
    .string()
    .min(1, "Institution is required.")
    .uuid("Must be a valid institution."),
  name: z
    .string()
    .min(2, "Faculty name must be at least 2 characters.")
    .max(255, "Faculty name must be 255 characters or fewer."),
  code: z
    .string()
    .min(2, "Code must be at least 2 characters.")
    .max(20, "Code must be 20 characters or fewer.")
    .regex(
      /^[A-Z0-9][A-Z0-9\-_]{1,19}$/,
      "Code must be uppercase letters, digits, hyphens, or underscores only."
    ),
  campus: z
    .string()
    .max(100, "Campus must be 100 characters or fewer.")
    .optional()
    .or(z.literal("")),
});

export type FacultyFormValues = z.infer<typeof facultySchema>;

interface FacultyFormProps {
  defaultValues?: Partial<Faculty>;
  /** When provided, the institution field is visible + populated with this list */
  institutions?: Institution[];
  /** When set, institution_id is locked to this value (QA Officer flow) */
  lockedInstitutionId?: string;
  onSubmit: (values: FacultyFormValues) => void | Promise<void>;
  onCancel: () => void;
  isPending?: boolean;
  isEdit?: boolean;
  serverErrors?: Record<string, string>;
  submitLabel?: string;
}

export function FacultyForm({
  defaultValues,
  institutions,
  lockedInstitutionId,
  onSubmit,
  onCancel,
  isPending = false,
  serverErrors,
  submitLabel = "Save",
}: FacultyFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors },
  } = useForm<FacultyFormValues>({
    resolver: zodResolver(facultySchema),
    defaultValues: {
      institution_id:
        defaultValues?.institution_id ?? lockedInstitutionId ?? "",
      name: defaultValues?.name ?? "",
      code: defaultValues?.code ?? "",
      campus: defaultValues?.campus ?? "",
    },
  });

  // Lock the institution when provided
  useEffect(() => {
    if (lockedInstitutionId) {
      setValue("institution_id", lockedInstitutionId);
    }
  }, [lockedInstitutionId, setValue]);

  // Propagate server errors
  useEffect(() => {
    if (!serverErrors) return;
    Object.entries(serverErrors).forEach(([field, message]) => {
      setError(field as keyof FacultyFormValues, {
        type: "server",
        message,
      });
    });
  }, [serverErrors, setError]);

  function handleCodeBlur(e: React.FocusEvent<HTMLInputElement>) {
    setValue("code", e.target.value.toUpperCase().trim(), {
      shouldValidate: true,
    });
  }

  const showInstitutionSelect =
    !lockedInstitutionId && institutions && institutions.length > 0;
  const showInstitutionLocked =
    !!lockedInstitutionId && institutions && institutions.length > 0;

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {/* Institution — SA sees a select; QA sees the locked name */}
      {showInstitutionSelect && (
        <div className="space-y-1.5">
          <Label htmlFor="institution_id">
            Institution <span className="text-destructive">*</span>
          </Label>
          <select
            id="institution_id"
            aria-invalid={!!errors.institution_id}
            aria-describedby={
              errors.institution_id ? "institution-error" : undefined
            }
            className={`flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring ${
              errors.institution_id ? "border-destructive" : "border-input"
            }`}
            {...register("institution_id")}
          >
            <option value="">Select an institution…</option>
            {institutions.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name} ({inst.code})
              </option>
            ))}
          </select>
          {errors.institution_id && (
            <p id="institution-error" role="alert" className="text-xs text-destructive">
              {errors.institution_id.message}
            </p>
          )}
        </div>
      )}

      {showInstitutionLocked && (
        <div className="space-y-1.5">
          <Label>Institution</Label>
          <p className="text-sm text-foreground rounded-md border border-input bg-muted px-3 py-2">
            {institutions.find((i) => i.id === lockedInstitutionId)?.name ??
              "Your institution"}
          </p>
          <input type="hidden" {...register("institution_id")} />
        </div>
      )}

      {/* Hidden when no institutions passed (should not happen in practice) */}
      {!showInstitutionSelect && !showInstitutionLocked && (
        <input type="hidden" {...register("institution_id")} />
      )}

      {/* Faculty Name */}
      <div className="space-y-1.5">
        <Label htmlFor="name">
          Faculty Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder="e.g. Faculty of Computing and Engineering"
          autoFocus
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

      {/* Faculty Code */}
      <div className="space-y-1.5">
        <Label htmlFor="code">
          Faculty Code <span className="text-destructive">*</span>
        </Label>
        <Input
          id="code"
          placeholder="e.g. FCE"
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

      {/* Campus */}
      <div className="space-y-1.5">
        <Label htmlFor="campus">Campus</Label>
        <Input
          id="campus"
          placeholder="e.g. Main Campus"
          aria-invalid={!!errors.campus}
          {...register("campus")}
          className={errors.campus ? "border-destructive" : ""}
        />
        {errors.campus && (
          <p role="alert" className="text-xs text-destructive">
            {errors.campus.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Optional. Identifies the physical campus this faculty belongs to.
        </p>
      </div>

      {/* Dean ID — deferred to Phase 3 (no user-listing endpoint yet) */}

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
