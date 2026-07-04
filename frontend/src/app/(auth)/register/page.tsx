import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata: Metadata = { title: "Request Access — AQAA" };

export default function RegisterPage() {
  return (
    <div className="w-full max-w-lg">
      {/* Brand */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Request Access</h1>
        <p className="text-white/60 text-sm mt-1">
          Academic Quality Assurance Agent — Institution Portal
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-2xl p-8">
        <RegisterForm />
      </div>

      <p className="text-center text-white/40 text-xs mt-6">
        Already have an account?{" "}
        <a href="/login" className="text-white/60 underline hover:text-white transition-colors">
          Sign in
        </a>
      </p>
    </div>
  );
}
