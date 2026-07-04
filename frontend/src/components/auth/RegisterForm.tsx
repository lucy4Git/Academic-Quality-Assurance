"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const ROLE_OPTIONS = [
  { value: "lecturer", label: "Lecturer" },
  { value: "programme_coordinator", label: "Programme Coordinator" },
  { value: "head_of_department", label: "Head of Department" },
  { value: "faculty_dean", label: "Faculty Dean" },
  { value: "quality_assurance_officer", label: "Quality Assurance Officer" },
] as const;

interface Fields {
  full_name: string;
  email: string;
  password: string;
  institution_name: string;
  role_requested: string;
  reason_for_access: string;
}

interface FieldErrors extends Partial<Record<keyof Fields, string>> {}

function validate(f: Fields): FieldErrors {
  const e: FieldErrors = {};
  if (!f.full_name.trim() || f.full_name.trim().length < 2)
    e.full_name = "Full name must be at least 2 characters.";
  if (!f.email.trim() || !EMAIL_RE.test(f.email.trim()))
    e.email = "Please enter a valid email address.";
  if (f.password.length < 8)
    e.password = "Password must be at least 8 characters.";
  else if (!/\d/.test(f.password))
    e.password = "Password must contain at least one digit.";
  else if (!/[A-Z]/.test(f.password))
    e.password = "Password must contain at least one uppercase letter.";
  if (!f.institution_name.trim())
    e.institution_name = "Institution name is required.";
  return e;
}

export function RegisterForm() {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>({
    full_name: "",
    email: "",
    password: "",
    institution_name: "",
    role_requested: "lecturer",
    reason_for_access: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(key: keyof Fields, value: string) {
    const next = { ...fields, [key]: value };
    setFields(next);
    if (submitted) {
      const errs = validate(next);
      setErrors(errs);
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);
    const errs = validate(fields);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fields.full_name.trim(),
          email: fields.email.trim(),
          password: fields.password,
          institution_name: fields.institution_name.trim(),
          role_requested: fields.role_requested,
          reason_for_access: fields.reason_for_access.trim() || undefined,
        }),
      });

      const data = await res.json() as { message?: string; email?: string; detail?: string };

      if (!res.ok) {
        if (res.status === 409) {
          toast.error("Email already registered", {
            description: "An account with this email already exists. Sign in instead.",
          });
        } else if (res.status === 403) {
          toast.error("Registration closed", {
            description: data.detail ?? "Public registration is currently closed.",
          });
        } else {
          toast.error("Registration failed", { description: data.detail });
        }
        return;
      }

      toast.success("Registration submitted!", {
        description: "Check your email for the verification code.",
      });

      const email = encodeURIComponent(fields.email.trim());
      router.push(`/verify-email?email=${email}`);
    } catch {
      toast.error("Connection error", {
        description: "Unable to connect to the server. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function field(
    id: keyof Fields,
    label: string,
    props: Partial<React.ComponentProps<typeof Input>> = {}
  ) {
    return (
      <div className="space-y-1.5">
        <Label htmlFor={id} className="text-sm font-medium text-foreground">
          {label}
        </Label>
        <Input
          id={id}
          value={fields[id]}
          onChange={(e) => update(id, e.target.value)}
          aria-invalid={errors[id] ? true : undefined}
          aria-describedby={errors[id] ? `${id}-error` : undefined}
          className={errors[id] ? "border-destructive focus-visible:ring-destructive" : ""}
          {...props}
        />
        {errors[id] && (
          <p id={`${id}-error`} role="alert" className="text-xs text-destructive mt-1">
            {errors[id]}
          </p>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground border-l-2 border-blue-500 pl-3 py-1">
          New accounts require email verification and administrator approval before access is granted.
        </p>

        {field("full_name", "Full name", { autoFocus: true, placeholder: "Dr. Jane Smith", autoComplete: "name" })}
        {field("email", "Email address", { type: "text", inputMode: "email", placeholder: "you@institution.ac.za", autoComplete: "email" })}

        {/* Password with toggle */}
        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm font-medium text-foreground">
            Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              value={fields.password}
              onChange={(e) => update("password", e.target.value)}
              autoComplete="new-password"
              placeholder="Min 8 chars, 1 uppercase, 1 digit"
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "password-error" : undefined}
              className={errors.password ? "border-destructive focus-visible:ring-destructive pr-10" : "pr-10"}
            />
            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p id="password-error" role="alert" className="text-xs text-destructive mt-1">
              {errors.password}
            </p>
          )}
        </div>

        {field("institution_name", "Institution name", { placeholder: "e.g. Tshwane University of Technology" })}

        {/* Role dropdown */}
        <div className="space-y-1.5">
          <Label htmlFor="role_requested" className="text-sm font-medium text-foreground">
            Requested role
          </Label>
          <select
            id="role_requested"
            value={fields.role_requested}
            onChange={(e) => update("role_requested", e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {ROLE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Reason */}
        <div className="space-y-1.5">
          <Label htmlFor="reason_for_access" className="text-sm font-medium text-foreground">
            Reason for access{" "}
            <span className="text-muted-foreground font-normal">(optional)</span>
          </Label>
          <textarea
            id="reason_for_access"
            value={fields.reason_for_access}
            onChange={(e) => update("reason_for_access", e.target.value)}
            placeholder="Brief explanation of why you need access…"
            rows={2}
            maxLength={500}
            className="flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
          />
        </div>

        <Button type="submit" className="w-full h-10 font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting…
            </>
          ) : (
            "Request Access"
          )}
        </Button>

        <p className="text-center text-xs text-muted-foreground">
          Already have an account?{" "}
          <a href="/login" className="text-primary hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </form>
  );
}
