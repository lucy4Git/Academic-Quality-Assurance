"use client";

import Link from "next/link";
import { Library, Upload, SearchCheck, AlertTriangle, GitBranch, ShieldCheck, Shield } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

const STAFF: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"];
const COORDINATOR_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator"];
const DEAN_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean"];
const QA_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer"];

const CARDS = [
  { label: "File Library", href: "/files", icon: Library, description: "Evidence files and documentation library", roles: STAFF },
  { label: "Upload Evidence", href: "/files/upload", icon: Upload, description: "Upload audit evidence and supporting documents", roles: COORDINATOR_AND_ABOVE },
  { label: "Audit Centre", href: "/audits", icon: SearchCheck, description: "AI-powered audit execution and history", roles: COORDINATOR_AND_ABOVE },
  { label: "Findings", href: "/findings", icon: AlertTriangle, description: "Review and manage audit findings", roles: STAFF },
  { label: "Workflow", href: "/workflow", icon: GitBranch, description: "Approval workflows and task routing", roles: STAFF },
  { label: "Approvals", href: "/approvals", icon: ShieldCheck, description: "Pending approvals and sign-off queue", roles: QA_AND_ABOVE },
  { label: "Accreditation", href: "/accreditation", icon: Shield, description: "Accreditation readiness and body submissions", roles: DEAN_AND_ABOVE },
];

export default function QualityWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quality</h1>
        <p className="text-muted-foreground mt-1">Evidence, audits, findings, and accreditation readiness.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map((card) => (
          <Link key={card.href} href={card.href} className="group block rounded-xl border bg-card p-5 hover:bg-accent hover:border-primary/30 transition-all duration-150">
            <card.icon className="h-6 w-6 mb-3 text-primary" />
            <p className="font-semibold text-card-foreground">{card.label}</p>
            <p className="text-sm text-muted-foreground mt-1">{card.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
