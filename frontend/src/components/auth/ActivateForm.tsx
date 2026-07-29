"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Eye, EyeOff, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TokenStatus {
  loading: boolean;
  valid: boolean | null;
  fullName: string | null;
  email: string | null;
  error: string | null;
}

interface PasswordFields {
  password: string;
  confirm: string;
}

function validatePassword(p: string): string | null {
  if (p.length < 8) return "Password must be at least 8 characters.";
  if (!/\d/.test(p)) return "Password must contain at least one digit.";
  if (!/[A-Z]/.test(p)) return "Password must contain at least one uppercase letter.";
  return null;
}

interface Props {
  token: string;
}

export function ActivateForm({ token }: Props) {
  const router = useRouter();
  const [tokenStatus, setTokenStatus] = useState<TokenStatus>({
    loading: true,
    valid: null,
    fullName: null,
    email: null,
    error: null,
  });
  const [fields, setFields] = useState<PasswordFields>({ password: "", confirm: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<PasswordFields>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) {
      setTokenStatus({ loading: false, valid: false, fullName: null, email: null, error: "No activation token provided." });
      return;
    }
    fetch(`/api/proxy/auth/activate/validate?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json() as { valid?: boolean; full_name?: string; email?: string; detail?: string };
        if (res.ok && data.valid) {
          setTokenStatus({ loading: false, valid: true, fullName: data.full_name ?? null, email: data.email ?? null, error: null });
        } else {
          setTokenStatus({ loading: false, valid: false, fullName: null, email: null, error: data.detail ?? "Invalid or expired activation link." });
        }
      })
      .catch(() => {
        setTokenStatus({ loading: false, valid: false, fullName: null, email: null, error: "Could not reach the server." });
      });
  }, [token]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const passError = validatePassword(fields.password);
    const errors: Partial<PasswordFields> = {};
    if (passError) errors.password = passError;
    if (fields.confirm !== fields.password) errors.confirm = "Passwords do not match.";
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/proxy/auth/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: fields.password }),
      });
      const data = await res.json() as { message?: string; email?: string; detail?: string };
      if (!res.ok) {
        toast.error("Activation failed", { description: data.detail });
        return;
      }
      setDone(true);
      toast.success("Account activated!", { description: "You can now sign in with your new password." });
      setTimeout(() => router.push("/login"), 2500);
    } catch {
      toast.error("Connection error", { description: "Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  }

  if (tokenStatus.loading) {
    return (
      <div className="flex flex-col items-center py-8 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Verifying your activation link…</p>
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex flex-col items-center py-8 gap-3 text-center">
        <CheckCircle2 className="h-12 w-12 text-green-500" />
        <h2 className="text-lg font-semibold">Account activated!</h2>
        <p className="text-sm text-muted-foreground">Redirecting you to sign in…</p>
      </div>
    );
  }

  if (!tokenStatus.valid) {
    return (
      <div className="flex flex-col items-center py-8 gap-4 text-center">
        <XCircle className="h-12 w-12 text-destructive" />
        <div>
          <h2 className="text-lg font-semibold text-foreground">Link invalid or expired</h2>
          <p className="text-sm text-muted-foreground mt-1">{tokenStatus.error}</p>
        </div>
        <a
          href="/activate/expired"
          className="text-sm text-primary underline hover:no-underline"
        >
          Request a new activation link
        </a>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      {tokenStatus.fullName && (
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Welcome, <strong>{tokenStatus.fullName}</strong>. Please set a password for{" "}
            <strong>{tokenStatus.email}</strong>.
          </p>
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="password" className="text-sm font-medium">New password</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            value={fields.password}
            onChange={(e) => setFields((f) => ({ ...f, password: e.target.value }))}
            autoComplete="new-password"
            placeholder="Min 8 chars, 1 uppercase, 1 digit"
            className={fieldErrors.password ? "border-destructive pr-10" : "pr-10"}
          />
          <button
            type="button"
            aria-label={showPassword ? "Hide password" : "Show password"}
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {fieldErrors.password && (
          <p className="text-xs text-destructive">{fieldErrors.password}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirm" className="text-sm font-medium">Confirm password</Label>
        <div className="relative">
          <Input
            id="confirm"
            type={showConfirm ? "text" : "password"}
            value={fields.confirm}
            onChange={(e) => setFields((f) => ({ ...f, confirm: e.target.value }))}
            autoComplete="new-password"
            placeholder="Re-enter your password"
            className={fieldErrors.confirm ? "border-destructive pr-10" : "pr-10"}
          />
          <button
            type="button"
            aria-label={showConfirm ? "Hide" : "Show"}
            onClick={() => setShowConfirm((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {fieldErrors.confirm && (
          <p className="text-xs text-destructive">{fieldErrors.confirm}</p>
        )}
      </div>

      <Button type="submit" className="w-full h-10 font-medium" disabled={isSubmitting}>
        {isSubmitting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Activating…
          </>
        ) : (
          "Set Password & Activate"
        )}
      </Button>
    </form>
  );
}
