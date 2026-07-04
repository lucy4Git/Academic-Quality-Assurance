import type { Metadata } from "next";
import { Suspense } from "react";
import { VerifyEmailForm } from "@/components/auth/VerifyEmailForm";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Verify Email — AQAA" };

export default function VerifyEmailPage() {
  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Verify Your Email</h1>
        <p className="text-white/60 text-sm mt-1">
          Enter the 6-digit code sent to your email address
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-2xl p-8">
        <Suspense
          fallback={
            <div className="space-y-5">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          }
        >
          <VerifyEmailForm />
        </Suspense>
      </div>

      <p className="text-center text-white/40 text-xs mt-6">
        AQAA — Academic Quality Assurance Agent
      </p>
    </div>
  );
}
