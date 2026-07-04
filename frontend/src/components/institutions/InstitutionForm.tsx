"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Institution } from "@/types";

// ── Validation schema (mirrors backend InstitutionCreate / InstitutionUpdate) ─
const institutionSchema = z.object({
  name: z
    .string()
    .min(2, "Institution name must be at least 2 characters.")
    .max(255, "Institution name must be 255 characters or fewer."),
  code: z
    .string()
    .min(2, "Code must be at least 2 characters.")
    .max(20, "Code must be 20 characters or fewer.")
    .regex(
      /^[A-Z0-9][A-Z0-9\-_]{1,19}$/,
      "Code must be uppercase letters, digits, hyphens, or underscores only."
    ),
  country: z
    .string()
    .max(100, "Country must be 100 characters or fewer.")
    .optional()
    .or(z.literal("")),
  address: z
    .string()
    .max(500, "Address must be 500 characters or fewer.")
    .optional()
    .or(z.literal("")),
  logo_url: z
    .string()
    .url("Please enter a valid URL.")
    .optional()
    .or(z.literal("")),
});

export type InstitutionFormValues = z.infer<typeof institutionSchema>;

interface InstitutionFormProps {
  defaultValues?: Partial<Institution>;
  onSubmit: (values: InstitutionFormValues) => void | Promise<void>;
  onCancel: () => void;
  isPending?: boolean;
  /** When true, the Code field is shown as read-only (edit mode where code rarely changes) */
  isEdit?: boolean;
  /** External field errors from server (e.g. 409 code conflict) */
  serverErrors?: Record<string, string>;
  submitLabel?: string;
}

export function InstitutionForm({
  defaultValues,
  onSubmit,
  onCancel,
  isPending = false,
  isEdit = false,
  serverErrors,
  submitLabel = "Save",
}: InstitutionFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors },
  } = useForm<InstitutionFormValues>({
    resolver: zodResolver(institutionSchema),
    defaultValues: {
      name: defaultValues?.name ?? "",
      code: defaultValues?.code ?? "",
      country: defaultValues?.country ?? "",
      address: defaultValues?.address ?? "",
      logo_url: defaultValues?.logo_url ?? "",
    },
  });

  // Propagate server-side field errors into the form
  useEffect(() => {
    if (!serverErrors) return;
    Object.entries(serverErrors).forEach(([field, message]) => {
      setError(field as keyof InstitutionFormValues, {
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

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {/* Institution Name */}
      <div className="space-y-1.5">
        <Label htmlFor="name">
          Institution Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder="e.g. Greenfield University"
          autoFocus={!isEdit}
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

      {/* Institution Code */}
      <div className="space-y-1.5">
        <Label htmlFor="code">
          Institution Code <span className="text-destructive">*</span>
        </Label>
        <Input
          id="code"
          placeholder="e.g. GFU"
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

      {/* Country */}
      <div className="space-y-1.5">
        <Label htmlFor="country">Country</Label>
        <Input
          id="country"
          placeholder="e.g. United Kingdom"
          aria-invalid={!!errors.country}
          {...register("country")}
          className={errors.country ? "border-destructive" : ""}
        />
        {errors.country && (
          <p role="alert" className="text-xs text-destructive">
            {errors.country.message}
          </p>
        )}
      </div>

      {/* Address */}
      <div className="space-y-1.5">
        <Label htmlFor="address">Address</Label>
        <Textarea
          id="address"
          placeholder="e.g. 1 University Way, Greenfield, GF1 1AA"
          rows={3}
          aria-invalid={!!errors.address}
          {...register("address")}
          className={errors.address ? "border-destructive" : ""}
        />
        {errors.address && (
          <p role="alert" className="text-xs text-destructive">
            {errors.address.message}
          </p>
        )}
      </div>

      {/* Logo URL */}
      <div className="space-y-1.5">
        <Label htmlFor="logo_url">Logo URL</Label>
        <Input
          id="logo_url"
          type="url"
          placeholder="https://example.com/logo.png"
          aria-invalid={!!errors.logo_url}
          {...register("logo_url")}
          className={errors.logo_url ? "border-destructive" : ""}
        />
        {errors.logo_url && (
          <p role="alert" className="text-xs text-destructive">
            {errors.logo_url.message}
          </p>
        )}
      </div>

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
