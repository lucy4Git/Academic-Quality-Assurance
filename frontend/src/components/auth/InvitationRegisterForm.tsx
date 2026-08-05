"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Fields {
  token: string;
  full_name: string;
  email: string;
  password: string;
}

interface FieldErrors extends Partial<Record<keyof Fields, string>> {}

function validate(f: Fields): FieldErrors {
  const e: FieldErrors = {};
  if (!f.token.trim()) e.token = "Invitation code is required.";
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
  return e;
}

export function InvitationRegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefillToken = searchParams?.get("token") ?? "";

  const [fields, setFields] = useState<Fields>({
    token: prefillToken,
    full_name: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(key: keyof Fields, value: string) {
    const next = { ...fields, [key]: value };
    setFields(next);
    if (submitted) setErrors(validate(next));
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
      const res = await fetch("/api/auth/register-with-invitation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: fields.token.trim(),
          full_name: fields.full_name.trim(),
          email: fields.email.trim(),
          password: fields.password,
        }),
      });

      const data = await res.json() as {
        message?: string;
        email?: string;
        requires_email_verification?: boolean;
        detail?: string;
      };

      if (!res.ok) {
        if (res.status === 404) {
          toast.error("Invalid invitation", {
            description: "This invitation code is invalid, expired, or has already been used.",
          });
        } else if (res.status === 409) {
          toast.error("Email already registered", {
            description: "An account with this email already exists. Sign in instead.",
          });
        } else if (res.status === 403) {
          toast.error("Invitation restricted", {
            description: data.detail ?? "Your email address does not match this invitation's restriction.",
          });
        } else {
          toast.error("Registration failed", { description: data.detail ?? "Please try again." });
        }
        return;
      }

      if (data.requires_email_verification) {
        router.push(`/verify-email?email=${encodeURIComponent(fields.email.trim())}`);
      } else {
        toast.success("Account created", { description: "You can now sign in." });
        router.push("/login");
      }
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
        <div className="rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm text-amber-800">
          <p className="font-medium mb-1">Staff &amp; External invitation</p>
          <p className="text-xs text-amber-700">
            Your institution administrator sent you an invitation code. Enter it below along with your details
            to create your account with the correct role and permissions.
          </p>
        </div>

        {field("token", "Invitation code", {
          autoFocus: !prefillToken,
          placeholder: "Paste your invitation code here",
          autoComplete: "off",
          spellCheck: false,
        })}
        {field("full_name", "Full name", {
          autoFocus: !!prefillToken,
          placeholder: "Dr. Jane Smith",
          autoComplete: "name",
        })}
        {field("email", "Email address", {
          type: "text",
          inputMode: "email",
          placeholder: "your@institution.ac.za",
          autoComplete: "email",
        })}
        {field("password", "Password", {
          type: "password",
          placeholder: "Min. 8 chars, 1 uppercase, 1 digit",
          autoComplete: "new-password",
        })}

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
