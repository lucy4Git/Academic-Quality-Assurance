"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Resolver } from "react-hook-form";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDepartments } from "@/hooks/useDepartments";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useFaculties } from "@/hooks/useFaculties";
import type { Programme, ProgrammeLevel, ProgrammeStatus } from "@/types";
import { PROGRAMME_LEVEL_LABELS, PROGRAMME_STATUS_LABELS } from "@/types";

const CODE_RE = /^[A-Z0-9][A-Z0-9\-_]{1,19}$/;

const STATUSES: ProgrammeStatus[] = [
  "active",
  "inactive",
  "pending_accreditation",
  "suspended",
];

export interface ProgrammeFormValues {
  institution_id?: string;
  faculty_id?: string;
  department_id: string;
  name: string;
  code: string;
  level: ProgrammeLevel;
  qualification_type: string;
  nqf_level: string;        // kept as string to simplify HTML input; coerced on submit
  duration_years: string;
  total_credits: string;
  status: ProgrammeStatus;
}

/**
 * Inline resolver — avoids @hookform/resolvers / zod@4 compatibility issues.
 */
const resolver: Resolver<ProgrammeFormValues> = async (values) => {
  const errors: Record<string, { message: string; type: string }> = {};

  if (!values.department_id)
    errors.department_id = { message: "Department is required.", type: "required" };

  const name = values.name?.trim();
  if (!name || name.length < 2)
    errors.name = { message: "Name must be at least 2 characters.", type: "minLength" };

  const code = values.code?.toUpperCase().trim();
  if (!code || code.length < 2)
    errors.code = { message: "Code must be at least 2 characters.", type: "minLength" };
  else if (!CODE_RE.test(code))
    errors.code = { message: "Uppercase letters, digits, hyphens or underscores only.", type: "pattern" };

  if (!values.level)
    errors.level = { message: "Level is required.", type: "required" };

  const nqf = values.nqf_level ? parseInt(values.nqf_level, 10) : NaN;
  if (values.nqf_level && (isNaN(nqf) || nqf < 1 || nqf > 10))
    errors.nqf_level = { message: "NQF level must be between 1 and 10.", type: "range" };

  const dur = values.duration_years ? parseInt(values.duration_years, 10) : NaN;
  if (values.duration_years && (isNaN(dur) || dur < 1 || dur > 10))
    errors.duration_years = { message: "Duration must be between 1 and 10 years.", type: "range" };

  const cred = values.total_credits ? parseInt(values.total_credits, 10) : NaN;
  if (values.total_credits && (isNaN(cred) || cred < 0 || cred > 9999))
    errors.total_credits = { message: "Credits must be between 0 and 9999.", type: "range" };

  if (Object.keys(errors).length) return { values: {} as never, errors };

  return {
    values: { ...values, code, name },
    errors: {},
  };
};

interface ProgrammeFormProps {
  defaultValues?: Partial<Programme>;
  lockedInstitutionId?: string;
  defaultDepartmentId?: string;
  onSubmit: (v: ProgrammeFormValues) => void | Promise<void>;
  onCancel: () => void;
  isPending?: boolean;
  isEdit?: boolean;
  serverErrors?: Record<string, string>;
  submitLabel?: string;
}

export function ProgrammeForm({
  defaultValues,
  lockedInstitutionId,
  defaultDepartmentId,
  onSubmit,
  onCancel,
  isPending = false,
  serverErrors,
  submitLabel = "Save",
}: ProgrammeFormProps) {
  const { data: institutions } = useInstitutions();
  const [selInstitutionId, setSelInstitutionId] = useState(lockedInstitutionId ?? "");
  const [selFacultyId, setSelFacultyId] = useState("");

  const { data: faculties } = useFaculties(selInstitutionId || undefined);
  const { data: departments } = useDepartments(selFacultyId || undefined);

  const {
    register, handleSubmit, setValue, setError, formState: { errors },
  } = useForm<ProgrammeFormValues>({
    resolver,
    defaultValues: {
      institution_id: lockedInstitutionId ?? "",
      faculty_id: "",
      department_id: defaultValues?.department_id ?? defaultDepartmentId ?? "",
      name: defaultValues?.name ?? "",
      code: defaultValues?.code ?? "",
      level: (defaultValues?.level as ProgrammeLevel) ?? "undergraduate",
      qualification_type: defaultValues?.qualification_type ?? "",
      nqf_level: defaultValues?.nqf_level?.toString() ?? "",
      duration_years: defaultValues?.duration_years?.toString() ?? "",
      total_credits: defaultValues?.total_credits?.toString() ?? "",
      status: (defaultValues?.status as ProgrammeStatus) ?? "active",
    },
  });

  useEffect(() => {
    if (!serverErrors) return;
    Object.entries(serverErrors).forEach(([f, m]) =>
      setError(f as keyof ProgrammeFormValues, { type: "server", message: m })
    );
  }, [serverErrors, setError]);

  function handleCodeBlur(e: React.FocusEvent<HTMLInputElement>) {
    setValue("code", e.target.value.toUpperCase().trim(), { shouldValidate: true });
  }

  const showInstSelect = !lockedInstitutionId;
  const instName = lockedInstitutionId
    ? institutions?.find((i) => i.id === lockedInstitutionId)?.name
    : undefined;

  const selectClass = (hasErr: boolean) =>
    `flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm disabled:opacity-50 ${
      hasErr ? "border-destructive" : "border-input"
    }`;

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {/* ── Institution ─────────────────────────────────────────────── */}
      {showInstSelect ? (
        <div className="space-y-1.5">
          <Label htmlFor="institution_id">Institution</Label>
          <select
            id="institution_id"
            value={selInstitutionId}
            onChange={(e) => {
              setSelInstitutionId(e.target.value);
              setSelFacultyId("");
              setValue("faculty_id", "");
              setValue("department_id", "");
            }}
            className={selectClass(false)}
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

      {/* ── Faculty ─────────────────────────────────────────────────── */}
      <div className="space-y-1.5">
        <Label htmlFor="faculty_id">Faculty</Label>
        <select
          id="faculty_id"
          value={selFacultyId}
          onChange={(e) => {
            setSelFacultyId(e.target.value);
            setValue("faculty_id", e.target.value);
            setValue("department_id", "");
          }}
          disabled={!selInstitutionId && !lockedInstitutionId}
          className={selectClass(false)}
        >
          <option value="">
            {selInstitutionId || lockedInstitutionId ? "Select a faculty…" : "Select institution first…"}
          </option>
          {faculties?.map((f) => (
            <option key={f.id} value={f.id}>{f.name} ({f.code})</option>
          ))}
        </select>
      </div>

      {/* ── Department ──────────────────────────────────────────────── */}
      <div className="space-y-1.5">
        <Label htmlFor="department_id">
          Department <span className="text-destructive">*</span>
        </Label>
        <select
          id="department_id"
          aria-invalid={!!errors.department_id}
          disabled={!selFacultyId}
          className={selectClass(!!errors.department_id)}
          {...register("department_id")}
        >
          <option value="">
            {selFacultyId ? "Select a department…" : "Select faculty first…"}
          </option>
          {departments?.map((d) => (
            <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
          ))}
        </select>
        {errors.department_id && (
          <p role="alert" className="text-xs text-destructive">{errors.department_id.message}</p>
        )}
      </div>

      {/* ── Programme Name ──────────────────────────────────────────── */}
      <div className="space-y-1.5">
        <Label htmlFor="prog-name">
          Programme Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="prog-name"
          placeholder="e.g. Bachelor of Computer Science"
          aria-invalid={!!errors.name}
          {...register("name")}
          className={errors.name ? "border-destructive" : ""}
        />
        {errors.name && <p role="alert" className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      {/* ── Code + Level (2-col) ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="prog-code">
            Code <span className="text-destructive">*</span>
          </Label>
          <Input
            id="prog-code"
            placeholder="e.g. BSC-CS"
            className={`font-mono uppercase ${errors.code ? "border-destructive" : ""}`}
            aria-invalid={!!errors.code}
            {...register("code")}
            onBlur={handleCodeBlur}
          />
          {errors.code && <p role="alert" className="text-xs text-destructive">{errors.code.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="prog-level">
            Level <span className="text-destructive">*</span>
          </Label>
          <select id="prog-level" className={selectClass(!!errors.level)} {...register("level")}>
            {(["undergraduate", "postgraduate", "doctoral"] as ProgrammeLevel[]).map((l) => (
              <option key={l} value={l}>{PROGRAMME_LEVEL_LABELS[l]}</option>
            ))}
          </select>
          {errors.level && <p role="alert" className="text-xs text-destructive">{errors.level.message}</p>}
        </div>
      </div>

      {/* ── Qualification Type ───────────────────────────────────────── */}
      <div className="space-y-1.5">
        <Label htmlFor="qual-type">Qualification Type</Label>
        <Input
          id="qual-type"
          placeholder="e.g. Bachelor of Science, Master of Arts"
          {...register("qualification_type")}
        />
      </div>

      {/* ── NQF Level + Duration + Credits (3-col) ─────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="nqf-level">NQF Level</Label>
          <Input
            id="nqf-level"
            type="number"
            min={1} max={10}
            placeholder="1–10"
            aria-invalid={!!errors.nqf_level}
            {...register("nqf_level")}
            className={errors.nqf_level ? "border-destructive" : ""}
          />
          {errors.nqf_level && <p role="alert" className="text-xs text-destructive">{errors.nqf_level.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="duration">Duration (years)</Label>
          <Input
            id="duration"
            type="number"
            min={1} max={10}
            placeholder="e.g. 3"
            aria-invalid={!!errors.duration_years}
            {...register("duration_years")}
            className={errors.duration_years ? "border-destructive" : ""}
          />
          {errors.duration_years && <p role="alert" className="text-xs text-destructive">{errors.duration_years.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="credits">Total Credits</Label>
          <Input
            id="credits"
            type="number"
            min={0} max={9999}
            placeholder="e.g. 360"
            aria-invalid={!!errors.total_credits}
            {...register("total_credits")}
            className={errors.total_credits ? "border-destructive" : ""}
          />
          {errors.total_credits && <p role="alert" className="text-xs text-destructive">{errors.total_credits.message}</p>}
        </div>
      </div>

      {/* ── Status ──────────────────────────────────────────────────── */}
      <div className="space-y-1.5">
        <Label htmlFor="prog-status">Status</Label>
        <select id="prog-status" className={selectClass(false)} {...register("status")}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{PROGRAMME_STATUS_LABELS[s]}</option>
          ))}
        </select>
      </div>

      {/* ── Actions ─────────────────────────────────────────────────── */}
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
