"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/auth.store";
import type { User } from "@/types";

// Email format check — used to show the inline validation message.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
}

function validate(email: string, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (!email.trim() || !EMAIL_RE.test(email.trim())) {
    errors.email = "Please enter a valid email address.";
  }
  if (!password) {
    errors.password = "Password is required.";
  }
  return errors;
}

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Field errors — only populated after the first submit attempt.
  const [errors, setErrors] = useState<FieldErrors>({});
  // Track whether the form has been submitted once so onChange re-validates.
  const [submitted, setSubmitted] = useState(false);

  // Re-validate a single field whenever the user types, but only after
  // the first submit (so errors never appear before they click Sign In).
  function handleEmailChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setEmail(val);
    if (submitted) {
      setErrors((prev) => {
        const next = { ...prev };
        if (val.trim() && EMAIL_RE.test(val.trim())) {
          delete next.email;
        } else {
          next.email = "Please enter a valid email address.";
        }
        return next;
      });
    }
  }

  function handlePasswordChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setPassword(val);
    if (submitted) {
      setErrors((prev) => {
        const next = { ...prev };
        if (val) {
          delete next.password;
        } else {
          next.password = "Password is required.";
        }
        return next;
      });
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);

    // Client-side validation
    const fieldErrors = validate(email, password);
    if (Object.keys(fieldErrors).length > 0) {
      setErrors(fieldErrors);
      return;
    }
    setErrors({});

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = (await res.json()) as { user?: User; detail?: string };

      if (!res.ok) {
        if (res.status === 401) {
          toast.error("Sign in failed", {
            description: "Invalid email or password. Please try again.",
          });
        } else if (res.status === 403) {
          toast.error("Account access restricted", {
            description:
              "Your account does not have access to this system. Contact your administrator.",
          });
        } else if (res.status === 429) {
          toast.error("Too many attempts", {
            description:
              "Too many sign-in attempts. Please wait a moment and try again.",
          });
        } else {
          toast.error("Service error", {
            description: "The service encountered an error. Please try again.",
          });
        }
        return;
      }

      if (data.user) {
        setUser(data.user);
      }

      // Hard navigation so the browser sends the new httpOnly cookie with
      // the very next request. router.push() alone can race against
      // router.refresh(); window.location.href guarantees a clean reload
      // that middleware and AppShell both see with the fresh token.
      const defaultDest = data.user?.role === "generic_user" ? "/workspace" : "/dashboard";
      const redirect = searchParams.get("redirect") ?? defaultDest;
      const safePath = redirect.startsWith("/") ? redirect : defaultDest;
      window.location.href = safePath;
    } catch {
      toast.error("Connection error", {
        description:
          "Unable to connect to the server. Check your connection and try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="space-y-5">
        {/* Email ---------------------------------------------------------- */}
        <div className="space-y-1.5">
          <Label
            htmlFor="email"
            className="text-sm font-medium text-foreground"
          >
            Email address
          </Label>
          {/*
           * type="text" + inputMode="email" prevents base-ui's Field.Control
           * from engaging the browser's native Constraint Validation API.
           * With type="email", base-ui fires typeMismatch on every keystroke
           * and forces aria-invalid="true" before the user finishes typing.
           * inputMode="email" preserves the optimised mobile keyboard.
           */}
          <Input
            id="email"
            type="text"
            inputMode="email"
            autoComplete="email"
            autoFocus
            placeholder="you@institution.ac.uk"
            value={email}
            onChange={handleEmailChange}
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "email-error" : undefined}
            className={
              errors.email
                ? "border-destructive focus-visible:ring-destructive"
                : ""
            }
          />
          {errors.email && (
            <p
              id="email-error"
              role="alert"
              className="text-xs text-destructive mt-1"
            >
              {errors.email}
            </p>
          )}
        </div>

        {/* Password ------------------------------------------------------- */}
        <div className="space-y-1.5">
          <Label
            htmlFor="password"
            className="text-sm font-medium text-foreground"
          >
            Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={handlePasswordChange}
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "password-error" : undefined}
              className={
                errors.password
                  ? "border-destructive focus-visible:ring-destructive pr-10"
                  : "pr-10"
              }
            />
            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.password && (
            <p
              id="password-error"
              role="alert"
              className="text-xs text-destructive mt-1"
            >
              {errors.password}
            </p>
          )}
        </div>

        {/* Submit ---------------------------------------------------------- */}
        <Button
          type="submit"
          className="w-full h-10 font-medium"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in…
            </>
          ) : (
            "Sign In"
          )}
        </Button>

        {/* Forgot password — Phase 3 */}
        <p className="text-center text-xs text-muted-foreground">
          Forgot your password?{" "}
          <span
            className="text-muted-foreground/50 cursor-not-allowed"
            title="Password reset is coming in a future release"
          >
            Reset password
          </span>
        </p>

        <p className="text-center text-xs text-muted-foreground">
          Don&apos;t have an account?{" "}
          <a href="/register" className="text-primary hover:underline">
            Request access
          </a>
        </p>
      </div>
    </form>
  );
}
