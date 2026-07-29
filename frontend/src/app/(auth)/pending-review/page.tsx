import type { Metadata } from "next";
import { Clock, Mail, CheckCircle2 } from "lucide-react";

export const metadata: Metadata = { title: "Request Received — AQAA" };

export default function PendingReviewPage({
  searchParams,
}: {
  searchParams: { email?: string };
}) {
  const email = searchParams.email ? decodeURIComponent(searchParams.email) : null;

  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4">
          <span className="text-3xl font-bold text-white tracking-tight">AQ</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Request Received</h1>
        <p className="text-white/60 text-sm mt-1">
          Academic Quality Assurance Agent
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-2xl p-8 space-y-6">
        <div className="flex flex-col items-center text-center space-y-3">
          <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center">
            <Clock className="w-7 h-7 text-amber-500" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">Pending Administrator Review</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Your access request has been submitted and is awaiting review by your
            institution&apos;s administrator.
          </p>
        </div>

        <div className="space-y-3">
          {[
            { icon: Mail, label: email ? `Verify ${email}` : "Verify your email", done: false, active: true },
            { icon: CheckCircle2, label: "Administrator approves your request", done: false, active: false },
            { icon: CheckCircle2, label: "Activation link sent to your email", done: false, active: false },
            { icon: CheckCircle2, label: "Set your password and sign in", done: false, active: false },
          ].map(({ icon: Icon, label, active }, i) => (
            <div
              key={i}
              className={`flex items-center gap-3 p-3 rounded-lg text-sm ${
                active
                  ? "bg-blue-50 text-blue-800 font-medium"
                  : "bg-gray-50 text-muted-foreground"
              }`}
            >
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                active ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-500"
              }`}>
                {i + 1}
              </span>
              {label}
            </div>
          ))}
        </div>

        {email && (
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800">
            <p className="font-medium mb-1">Next step</p>
            <p className="text-xs text-blue-700">
              Check <strong>{email}</strong> for a verification code and enter it to
              confirm your email address.
            </p>
            <a
              href={`/verify-email?email=${encodeURIComponent(email)}`}
              className="inline-block mt-2 text-xs font-medium text-blue-700 underline hover:text-blue-900"
            >
              Go to email verification →
            </a>
          </div>
        )}

        <p className="text-center text-xs text-muted-foreground">
          Once an administrator approves your request, you will receive an activation
          link at your registered email address.
        </p>

        <p className="text-center text-xs text-muted-foreground">
          <a href="/login" className="text-primary hover:underline">
            Back to sign in
          </a>
        </p>
      </div>
    </div>
  );
}
