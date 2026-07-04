"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Resolver } from "react-hook-form";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useFaculties } from "@/hooks/useFaculties";
import { useDepartments } from "@/hooks/useDepartments";
import { useProgrammes } from "@/hooks/useProgrammes";
import type { Module } from "@/types";
import { SEMESTER_OPTIONS } from "@/types";

const CODE_RE = /^[A-Z0-9][A-Z0-9\-_]{1,19}$/;
const YEAR_RE = /^\d{4}\/\d{4}$/;

export interface ModuleFormValues {
  institution_id: string;
  faculty_id: string;
  department_id: string;
  programme_id: string;
  name: string;
  code: string;
  credits: string;
  semester: string;
  academic_year: string;
}

const resolver: Resolver<ModuleFormValues> = async (values) => {
  const errors: Record<string, { message: string; type: string }> = {};

  if (!values.programme_id)
    errors.programme_id = { message: "Programme is required.", type: "required" };

  const name = values.name?.trim();
  if (!name || name.length < 2)
    errors.name = { message: "Name must be at least 2 characters.", type: "minLength" };

  const code = values.code?.toUpperCase().trim();
  if (!code || code.length < 2)
    errors.code = { message: "Code must be at least 2 characters.", type: "minLength" };
  else if (!CODE_RE.test(code))
    errors.code = {
      message: "Uppercase letters, digits, hyphens or underscores only.",
      type: "pattern",
    };

  const credits = parseInt(values.credits, 10);
  if (values.credits === "" || isNaN(credits) || credits < 0 || credits > 240)
    errors.credits = { message: "Credits must be between 0 and 240.", type: "range" };

  if (!values.semester?.trim())
    errors.semester = { message: "Semester is required.", type: "required" };

  const year = values.academic_year?.trim();
  if (!YEAR_RE.test(year)) {
    errors.academic_year = {
      message: "Academic year must be in format YYYY/YYYY (e.g. 2024/2025).",
      type: "pattern",
    };
  } else {
    const start = parseInt(year.slice(0, 4), 10);
    const end = parseInt(year.slice(5), 10);
    if (end !== start + 1)
      errors.academic_year = {
        message: "End year must be exactly one year after start year.",
        type: "pattern",
      };
  }

  if (Object.keys(errors).length) return { values: {} as never, errors };

  return {
    values: { ...values, code: values.code.toUpperCase().trim(), name: name },
    errors: {},
  };
};

interface ModuleFormProps {
  defaultValues?: Partial<Module>;
  lockedInstitutionId?: string;
  defaultProgrammeId?: string;
  onSubmit: (v: ModuleFormValues) => void | Promise<void>;
  onCancel: () => void;
  isPending?: boolean;
  isEdit?: boolean;
  serverErrors?: Record<string, string>;
  submitLabel?: string;
}

export function ModuleForm({
  defaultValues,
  lockedInstitutionId,
  defaultProgrammeId,
  onSubmit,
  onCancel,
  isPending = false,
  isEdit = false,
  serverErrors,
  submitLabel = "Save",
}: ModuleFormProps) {
  const { data: institutions } = useInstitutions();
  const [selInstId, setSelInstId] = useState(lockedInstitutionId ?? "");
  const [selFacultyId, setSelFacultyId] = useState("");
  const [selDeptId, setSelDeptId] = useState("");

  const { data: faculties } = useFaculties(selInstId || undefined);
  const { data: departments } = useDepartments(selFacultyId || undefined);
  const { data: programmes } = useProgrammes(selDeptId || undefined);

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    watch,
    formState: { errors },
  } = useForm<ModuleFormValues>({
    resolver,
    defaultValues: {
      institution_id: lockedInstitutionId ?? "",
      faculty_id: "",
      department_id: "",
      programme_id: defaultValues?.programme_id ?? defaultProgrammeId ?? "",
      name: defaultValues?.name ?? "",
      code: defaultValues?.code ?? "",
      credits: defaultValues?.credits?.toString() ?? "0",
      semester: defaultValues?.semester ?? "",
      academic_year: defaultValues?.academic_year ?? "",
    },
  });

  useEffect(() => {
    if (!serverErrors) return;
    Object.entries(serverErrors).forEach(([f, m]) =>
      setError(f as keyof ModuleFormValues, { type: "server", message: m })
    );
  }, [serverErrors, setError]);

  function handleCodeBlur(e: React.FocusEvent<HTMLInputElement>) {
    setValue("code", e.target.value.toUpperCase().trim(), { shouldValidate: true });
  }

  const cls = (err: boolean) =>
    `flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm disabled:opacity-50 ${
      err ? "border-destructive" : "border-input"
    }`;

  const showInstSelect = !lockedInstitutionId;
  const instName = lockedInstitutionId
    ? institutions?.find((i) => i.id === lockedInstitutionId)?.name
    : undefined;

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {/* Institution */}
      {showInstSelect ? (
        <div className="space-y-1.5">
          <Label htmlFor="m-inst">Institution</Label>
          <select
            id="m-inst"
            value={selInstId}
            onChange={(e) => {
              setSelInstId(e.target.value);
              setSelFacultyId("");
              setSelDeptId("");
              setValue("faculty_id", "");
              setValue("department_id", "");
              setValue("programme_id", "");
            }}
            className={cls(false)}
          >
            <option value="">Select an institution…</option>
            {institutions?.map((i) => (
              <option key={i.id} value={i.id}>{i.name} ({i.code})</option>
            ))}
          </select>
        </div>
      ) : (
        <div className="space-y-1.5">
          <Label>Institution</Label>
          <p className="text-sm text-foreground rounded-md border border-input bg-muted px-3 py-2">
            {instName ?? "Your institution"}
          </p>
        </div>
      )}

      {/* Faculty */}
      <div className="space-y-1.5">
        <Label htmlFor="m-fac">Faculty</Label>
        <select
          id="m-fac"
          value={selFacultyId}
          disabled={!selInstId && !lockedInstitutionId}
          onChange={(e) => {
            setSelFacultyId(e.target.value);
            setSelDeptId("");
            setValue("faculty_id", e.target.value);
            setValue("department_id", "");
            setValue("programme_id", "");
          }}
          className={cls(false)}
        >
          <option value="">
            {selInstId || lockedInstitutionId ? "Select a faculty…" : "Select institution first…"}
          </option>
          {faculties?.map((f) => (
            <option key={f.id} value={f.id}>{f.name} ({f.code})</option>
          ))}
        </select>
      </div>

      {/* Department */}
      <div className="space-y-1.5">
        <Label htmlFor="m-dept">Department</Label>
        <select
          id="m-dept"
          value={selDeptId}
          disabled={!selFacultyId}
          onChange={(e) => {
            setSelDeptId(e.target.value);
            setValue("department_id", e.target.value);
            setValue("programme_id", "");
          }}
          className={cls(false)}
        >
          <option value="">
            {selFacultyId ? "Select a department…" : "Select faculty first…"}
          </option>
          {departments?.map((d) => (
            <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
          ))}
        </select>
      </div>

      {/* Programme */}
      <div className="space-y-1.5">
        <Label htmlFor="m-prog">
          Programme <span className="text-destructive">*</span>
        </Label>
        <select
          id="m-prog"
          aria-invalid={!!errors.programme_id}
          disabled={!selDeptId && !isEdit}
          className={cls(!!errors.programme_id)}
          {...register("programme_id")}
        >
          <option value="">
            {selDeptId || isEdit ? "Select a programme…" : "Select department first…"}
          </option>
          {programmes?.map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
          ))}
        </select>
        {errors.programme_id && (
          <p role="alert" className="text-xs text-destructive">{errors.programme_id.message}</p>
        )}
      </div>

      {/* Name + Code */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="m-name">
            Module Name <span className="text-destructive">*</span>
          </Label>
          <Input
            id="m-name"
            placeholder="e.g. Introduction to Programming"
            aria-invalid={!!errors.name}
            {...register("name")}
            className={errors.name ? "border-destructive" : ""}
          />
          {errors.name && (
            <p role="alert" className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="m-code">
            Code <span className="text-destructive">*</span>
          </Label>
          <Input
            id="m-code"
            placeholder="e.g. CS101"
            className={`font-mono uppercase ${errors.code ? "border-destructive" : ""}`}
            aria-invalid={!!errors.code}
            {...register("code")}
            onBlur={handleCodeBlur}
          />
          {errors.code && (
            <p role="alert" className="text-xs text-destructive">{errors.code.message}</p>
          )}
        </div>
      </div>

      {/* Credits + Semester + Academic Year */}
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="m-credits">
            Credits <span className="text-destructive">*</span>
          </Label>
          <Input
            id="m-credits"
            type="number"
            min={0}
            max={240}
            placeholder="e.g. 20"
            aria-invalid={!!errors.credits}
            {...register("credits")}
            className={errors.credits ? "border-destructive" : ""}
          />
          {errors.credits && (
            <p role="alert" className="text-xs text-destructive">{errors.credits.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="m-semester">
            Semester <span className="text-destructive">*</span>
          </Label>
          <select
            id="m-semester"
            aria-invalid={!!errors.semester}
            className={cls(!!errors.semester)}
            {...register("semester")}
          >
            <option value="">Select…</option>
            {SEMESTER_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {errors.semester && (
            <p role="alert" className="text-xs text-destructive">{errors.semester.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="m-year">
            Academic Year <span className="text-destructive">*</span>
          </Label>
          <Input
            id="m-year"
            placeholder="2024/2025"
            aria-invalid={!!errors.academic_year}
            aria-describedby={errors.academic_year ? "year-err" : "year-hint"}
            {...register("academic_year")}
            className={errors.academic_year ? "border-destructive" : ""}
          />
          {errors.academic_year ? (
            <p id="year-err" role="alert" className="text-xs text-destructive">
              {errors.academic_year.message}
            </p>
          ) : (
            <p id="year-hint" className="text-xs text-muted-foreground">
              Format: YYYY/YYYY
            </p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-2 border-t">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
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
