import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <div className="w-full max-w-md">
      {/* Logo / Brand */}
      <div className="text-center mb-7">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#1d3d35] mb-4 shadow-lg shadow-[#1d3d35]/15">
          <span className="text-sm font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
        <p className="text-[#686c67] text-sm mt-2">Continue your academic quality work with AQAA</p>
      </div>

      {/* Login card */}
      <div className="rounded-3xl border border-black/[0.08] bg-white p-7 shadow-[0_24px_70px_-45px_rgba(20,50,42,.5)] sm:p-8">
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

      <p className="text-center text-[#777b75] text-xs mt-6">
        AQAA · Evidence. Judgement. Assurance.
      </p>
    </div>
  );
}
