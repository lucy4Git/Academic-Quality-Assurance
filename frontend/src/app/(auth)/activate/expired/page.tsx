"use client";

import { useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function ActivationExpiredPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!EMAIL_RE.test(email.trim())) {
      toast.error("Please enter a valid email address.");
      return;
    }
    setIsSubmitting(true);
    try {
      await fetch("/api/proxy/auth/activate/resend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      setSent(true);
    } catch {
      toast.error("Connection error", { description: "Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Activation Link Expired</h1>
        <p className="text-white/60 text-sm mt-1">
          Academic Quality Assurance Agent
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-2xl p-8">
        {sent ? (
          <div className="flex flex-col items-center text-center gap-4 py-4">
            <RefreshCw className="h-12 w-12 text-primary" />
            <h2 className="text-lg font-semibold">Check your inbox</h2>
            <p className="text-sm text-muted-foreground">
              If <strong>{email}</strong> is registered and approved, a new activation
              link has been sent. It expires in 48 hours.
            </p>
            <a href="/login" className="text-sm text-primary underline">
              Back to sign in
            </a>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <p className="text-sm text-muted-foreground">
              Activation links expire after 48 hours. Enter your email to receive a
              new one — your approval status will not be affected.
            </p>

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">Email address</Label>
              <Input
                id="email"
                type="text"
                inputMode="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                autoComplete="email"
                placeholder="you@institution.ac.za"
              />
            </div>

            <Button type="submit" className="w-full h-10 font-medium" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending…
                </>
              ) : (
                "Resend Activation Link"
              )}
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              <a href="/login" className="text-primary hover:underline">Back to sign in</a>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
