"use client";

import Link from "next/link";
import { Brain, BrainCircuit, Calculator, Building2 } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

const STAFF: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"];

const CARDS = [
  { label: "AI Workspace", href: "/ai-workspace", icon: Brain, description: "Conversational AI with citation verification", roles: STAFF },
  { label: "AI QA Assistant", href: "/ai-assistant", icon: BrainCircuit, description: "Guided QA audit assistance and recommendations", roles: STAFF },
  { label: "Qualification Intelligence", href: "/qualification-intelligence", icon: Calculator, description: "Programme and module quality analysis", roles: STAFF },
  { label: "Institution Workspace", href: "/workspace", icon: Building2, description: "Institution-wide AI analysis and planning", roles: STAFF },
];

export default function AiWorkspaceLandingPage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI</h1>
        <p className="text-muted-foreground mt-1">AI-powered quality assurance workspaces and assistants.</p>
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
