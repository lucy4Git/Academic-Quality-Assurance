"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, GraduationCap, Briefcase } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InvitationRegisterForm } from "./InvitationRegisterForm";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Path = "student" | "invitation";

interface Fields {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
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

function PathSelector({ selected, onSelect }: { selected: Path; onSelect: (p: Path) => void }) {
  const paths: { id: Path; icon: React.ReactNode; label: string; sub: string }[] = [
    {
      id: "student",
      icon: <GraduationCap className="h-5 w-5" />,
      label: "New Account",
      sub: "Register with your email address",
    },
    {
      id: "invitation",
      icon: <Briefcase className="h-5 w-5" />,
      label: "Staff / External",
      sub: "I have an invitation code from my institution",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 mb-4">
      {paths.map((p) => (
        <button
          key={p.id}
          type="button"
          onClick={() => onSelect(p.id)}
          className={[
            "flex flex-col items-start gap-1 rounded-lg border p-3 text-left transition-colors",
            selected === p.id
              ? "border-primary bg-primary/5 text-primary"
              : "border-border bg-white text-foreground hover:border-primary/40",
          ].join(" ")}
        >
          <span className={selected === p.id ? "text-primary" : "text-muted-foreground"}>
            {p.icon}
          </span>
          <span className="text-sm font-medium leading-none">{p.label}</span>
          <span className="text-[11px] text-muted-foreground leading-tight">{p.sub}</span>
        </button>
      ))}
    </div>
  );
}

function StudentForm() {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
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
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fields.full_name.trim(),
          email: fields.email.trim(),
          password: fields.password,
        }),
      });

      const data = await res.json() as { message?: string; email?: string; detail?: string; requires_verification?: boolean };

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

      if (data.requires_verification) {
        // Verification mode active (production) — redirect to verify page
        router.push(`/verify-email?email=${encodeURIComponent(fields.email.trim())}`);
      } else {
        // Staging/pilot: account active immediately
        toast.success("Account created", {
          description: "Your account has been created. You can now sign in.",
        });
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
        {field("full_name", "Full name", { autoFocus: true, placeholder: "Jane Smith", autoComplete: "name" })}
        {field("email", "Email address", { type: "text", inputMode: "email", placeholder: "you@example.com", autoComplete: "email" })}
        {field("password", "Password", { type: "password", placeholder: "Min. 8 chars, 1 uppercase, 1 digit", autoComplete: "new-password" })}
        {field("confirm_password", "Confirm password", { type: "password", placeholder: "Re-enter your password", autoComplete: "new-password" })}

        <p className="text-xs text-muted-foreground">
          Your account will be created with student access. Institution-linked or privileged
          access requires an invitation — use the{" "}
          <strong>Staff / External</strong> tab.
        </p>

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
          <a href="/login" className="text-primary hover:underline">Sign in</a>
        </p>
      </div>
    </form>
  );
}

export function RegisterForm() {
  const [path, setPath] = useState<Path>("student");

  return (
    <div>
      <PathSelector selected={path} onSelect={setPath} />
      {path === "student" ? <StudentForm /> : <InvitationRegisterForm />}
    </div>
  );
}
