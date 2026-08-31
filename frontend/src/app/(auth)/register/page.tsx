import type { Metadata } from "next";
import { GenericRegisterForm } from "@/components/auth/GenericRegisterForm";

export const metadata: Metadata = { title: "Create Account — AQAA" };

export default function RegisterPage() {
  return (
    <div className="w-full max-w-md">
      {/* Brand */}
      <div className="text-center mb-7">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#1d3d35] mb-4 shadow-lg shadow-[#1d3d35]/15">
          <span className="text-sm font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Start with AQAA</h1>
        <p className="text-[#686c67] text-sm mt-2">
          Create your academic quality assurance workspace
        </p>
      </div>

      <div className="rounded-3xl border border-black/[0.08] bg-white p-7 shadow-[0_24px_70px_-45px_rgba(20,50,42,.5)] sm:p-8">
        <GenericRegisterForm />
      </div>

      <p className="text-center text-[#777b75] text-xs mt-6">
        Already have an account?{" "}
        <a href="/login" className="font-medium text-[#1d3d35] underline underline-offset-4">
          Sign in
        </a>
      </p>
    </div>
  );
}
