import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <div className="w-full max-w-md">
      {/* Logo / Brand */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">
          Academic Quality Assurance
        </h1>
        <p className="text-white/60 text-sm mt-1">
          Sign in to your institution&apos;s QA platform
        </p>
      </div>

      {/* Login card */}
      <div className="bg-white rounded-xl shadow-2xl p-8">
        {/* Suspense required because LoginForm uses useSearchParams() */}
        <Suspense
          fallback={
            <div className="space-y-5">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          }
        >
          <LoginForm />
        </Suspense>
      </div>

      <p className="text-center text-white/40 text-xs mt-6">
        AQAA — Academic Quality Assurance Agent
      </p>
    </div>
  );
}
