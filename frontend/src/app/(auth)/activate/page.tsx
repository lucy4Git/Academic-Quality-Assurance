import type { Metadata } from "next";
import { ActivateForm } from "@/components/auth/ActivateForm";

export const metadata: Metadata = { title: "Activate Account — AQAA" };

export default function ActivatePage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  const token = searchParams.token ?? "";
  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Activate Your Account</h1>
        <p className="text-white/60 text-sm mt-1">
          Academic Quality Assurance Agent — Set your password
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-2xl p-8">
        <ActivateForm token={token} />
      </div>
    </div>
  );
}
