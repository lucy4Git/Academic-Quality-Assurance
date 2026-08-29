"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, GraduationCap, Briefcase, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Persona = "quality_assurance_officer" | "lecturer";

interface Fields {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  persona: Persona | null;
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
  if (!f.persona)
    e.persona = "Please select your role.";
  return e;
}

function PersonaSelector({
  selected,
  onSelect,
}: {
  selected: Persona | null;
  onSelect: (p: Persona) => void;
}) {
  const personas: {
    id: Persona;
    icon: React.ReactNode;
    title: string;
    desc: string;
  }[] = [
    {
      id: "quality_assurance_officer",
      icon: <ShieldCheck className="h-5 w-5" />,
      title: "QA Officer",
      desc: "Review modules, check compliance",
    },
    {
      id: "lecturer",
      icon: <GraduationCap className="h-5 w-5" />,
      title: "Lecturer",
      desc: "Upload evidence, check findings",
    },
  ];

  return (
    <div>
      <Label className="text-sm font-medium text-foreground mb-2 block">
        What best describes your work?
      </Label>
      <div className="grid grid-cols-2 gap-3">
        {personas.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            className={[
              "flex flex-col items-start gap-2 rounded-lg border-2 p-3 text-left transition-all",
              selected === p.id
                ? "border-primary bg-primary/5"
                : "border-border bg-white hover:border-primary/40",
            ].join(" ")}
          >
            <span className={selected === p.id ? "text-primary" : "text-muted-foreground"}>
              {p.icon}
            </span>
            <div>
              <span className="text-sm font-medium leading-none text-foreground">
                {p.title}
              </span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block">
                {p.desc}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

export function GenericRegisterForm() {
  const router = useRouter();
  const [fields, setFields] = useState<Fields>({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    persona: null,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(key: keyof Fields, value: string | Persona | null) {
    setFields((current) => ({ ...current, [key]: value } as Fields));
    if (submitted) setErrors((current) => ({ ...current, [key]: undefined }));
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
          persona: fields.persona,
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
        description: "Your account has been created. Proceeding to setup...",
      });
      const params = new URLSearchParams({
        registered: "1",
        email: fields.email.trim(),
        redirect: "/onboarding",
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
    id: keyof Omit<Fields, "persona">,
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
          {field("full_name", "Full name", {
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

        <div className="border-t pt-4">
          <PersonaSelector selected={fields.persona} onSelect={(p) => update("persona", p)} />
          {errors.persona && (
            <p className="text-xs text-destructive mt-2">{errors.persona}</p>
          )}
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
