"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Fields {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  work_focus: "review" | "prepare" | "";
}

interface FieldErrors extends Partial<Record<keyof Fields, string>> {}

function validate(f: Fields): FieldErrors {
  const e: FieldErrors = {};
  if (!f.full_name.trim() || f.full_name.trim().length < 2)
    e.full_name = "Full name must be at least 2 characters.";
  if (!f.email.trim() || !EMAIL_RE.test(f.email.trim()))
    e.email = "Please enter a valid email address.";
  if (!f.password || f.password.length < 8)
    e.password = "Password must be at least 8 characters.";
  else if (!/\d/.test(f.password))
    e.password = "Password must contain at least one digit.";
  else if (!/[A-Z]/.test(f.password))
    e.password = "Password must contain at least one uppercase letter.";
  if (f.confirm_password !== f.password)
    e.confirm_password = "Passwords do not match.";
  return e;
}

export function GenericRegisterForm() {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    work_focus: "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(key: keyof Fields, value: string) {
    setFields((current) => ({ ...current, [key]: value } as Fields));
    if (submitted) setErrors((current) => ({ ...current, [key]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);
    const errs = validate(fields);
    if (!fields.work_focus) {
      toast.error("Tell us about your work focus", { description: "Choose the option that best describes your day-to-day QA work." });
      return;
    }
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
          qa_interests: fields.work_focus === "review" ? ["review_evidence", "identify_missing"] : ["prepare_evidence", "respond_findings"],
          evidence_types: ["module_guides", "assessments"],
          work_focus_signals: fields.work_focus === "review" ? ["review_evidence", "identify_missing"] : ["prepare_evidence", "module_owner"],
        }),
      });

      const data = await res.json() as {
        message?: string;
        email?: string;
        detail?: string | Array<{ msg?: string }>;
        requires_verification?: boolean;
      };
      const detail = typeof data.detail === "string"
        ? data.detail
        : data.detail?.map((item) => item.msg).filter(Boolean).join(" ");

      if (!res.ok) {
        if (res.status === 409) {
          toast.error("Email already registered", {
            description: "An account with this email already exists. Sign in instead.",
          });
        } else if (res.status === 403) {
          toast.error("Registration closed", {
            description: detail ?? "Public registration is currently closed.",
          });
        } else {
          toast.error("Registration failed", { description: detail });
        }
        return;
      }

      toast.success("Account created", {
        description: "Your account and private workspace are ready. Sign in to continue.",
      });
      const params = new URLSearchParams({
        registered: "1",
        email: fields.email.trim(),
        redirect: "/workspace",
      });
      router.push(`/login?${params.toString()}`);
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
          value={fields[id] as string}
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
        <div className="space-y-3">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-foreground">What best describes your work?</legend>
            <p className="text-xs text-muted-foreground">This tailors your workspace and never changes permissions.</p>
            {([["review", "I review quality evidence and identify gaps"], ["prepare", "I prepare evidence and respond to findings"]] as const).map(([value, label]) => (
              <label key={value} className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm hover:bg-muted/50">
                <input type="radio" name="work_focus" value={value} checked={fields.work_focus === value} onChange={() => update("work_focus", value)} className="mt-0.5" />
                <span>{label}</span>
              </label>
            ))}
          </fieldset>          {field("full_name", "Full name", {
            autoFocus: true,
            placeholder: "Your name",
            autoComplete: "name",
          })}
          {field("email", "Email address", {
            type: "text",
            inputMode: "email",
            placeholder: "you@example.com",
            autoComplete: "email",
          })}
          {field("password", "Password", {
            type: "password",
            placeholder: "Min. 8 chars, 1 uppercase, 1 digit",
            autoComplete: "new-password",
          })}
          {field("confirm_password", "Confirm password", {
            type: "password",
            placeholder: "Re-enter your password",
            autoComplete: "new-password",
          })}
        </div>

        <Button type="submit" className="w-full h-10 font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating account…
            </>
          ) : (
            "Create Account"
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
