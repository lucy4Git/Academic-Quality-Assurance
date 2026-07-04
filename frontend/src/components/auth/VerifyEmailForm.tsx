"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email") ?? "";

  const [email, setEmail] = useState(emailParam);
  const [code, setCode] = useState("");
  const [codeError, setCodeError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [verified, setVerified] = useState(false);
  const [approvalStatus, setApprovalStatus] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!code.trim() || code.trim().length < 4) {
      setCodeError("Please enter your verification code.");
      return;
    }
    setCodeError("");
    setIsSubmitting(true);

    try {
      const res = await fetch("/api/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), code: code.trim() }),
      });

      const data = await res.json() as {
        message?: string;
        is_active?: boolean;
        approval_status?: string;
        detail?: string;
      };

      if (!res.ok) {
        toast.error("Verification failed", {
          description: data.detail ?? "Invalid or expired code. Please try again.",
        });
        setCodeError("Invalid or expired verification code.");
        return;
      }

      setVerified(true);
      setApprovalStatus(data.approval_status ?? null);

      if (data.is_active) {
        toast.success("Email verified!", {
          description: "Your account is now active. Redirecting to sign in…",
        });
        setTimeout(() => router.push("/login"), 2500);
      } else {
        toast.success("Email verified!", {
          description: "Your account is pending administrator approval.",
        });
      }
    } catch {
      toast.error("Connection error", {
        description: "Unable to connect to the server. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResend() {
    if (!email.trim()) {
      toast.error("Email required", { description: "Please enter your email address." });
      return;
    }
    setIsResending(true);
    try {
      await fetch("/api/auth/verify-email?action=resend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      toast.success("Code resent", {
        description: "If this email is registered and unverified, a new code has been sent.",
      });
    } catch {
      toast.error("Connection error", {
        description: "Unable to resend. Please try again.",
      });
    } finally {
      setIsResending(false);
    }
  }

  if (verified) {
    return (
      <div className="text-center space-y-4 py-4">
        <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto" />
        <h2 className="text-lg font-semibold text-foreground">Email Verified</h2>
        {approvalStatus === "approved" ? (
          <p className="text-sm text-muted-foreground">
            Your account is now active. Redirecting to sign in…
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Your email has been verified. Your account is pending administrator approval.
            </p>
            <p className="text-xs text-muted-foreground">
              You will receive an email notification once your account is approved.
            </p>
            <Button variant="outline" className="mt-4 w-full" onClick={() => router.push("/login")}>
              Back to Sign In
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="space-y-5">
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code from the verification email sent to your address.
        </p>

        {!emailParam && (
          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-sm font-medium text-foreground">
              Email address
            </Label>
            <Input
              id="email"
              type="text"
              inputMode="email"
              autoComplete="email"
              placeholder="you@institution.ac.za"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="code" className="text-sm font-medium text-foreground">
            Verification code
          </Label>
          <Input
            id="code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            placeholder="123456"
            maxLength={10}
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              if (codeError) setCodeError("");
            }}
            aria-invalid={codeError ? true : undefined}
            aria-describedby={codeError ? "code-error" : undefined}
            className={`text-center text-xl tracking-widest font-mono ${codeError ? "border-destructive focus-visible:ring-destructive" : ""}`}
          />
          {codeError && (
            <p id="code-error" role="alert" className="text-xs text-destructive mt-1">
              {codeError}
            </p>
          )}
        </div>

        <Button type="submit" className="w-full h-10 font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Verifying…
            </>
          ) : (
            "Verify Email"
          )}
        </Button>

        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={handleResend}
            disabled={isResending}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            {isResending ? "Resending…" : "Didn't receive a code? Resend"}
          </button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          <a href="/login" className="text-primary hover:underline">
            Back to Sign In
          </a>
        </p>
      </div>
    </form>
  );
}
