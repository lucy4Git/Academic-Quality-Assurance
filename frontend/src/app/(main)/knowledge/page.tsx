"use client";

import Link from "next/link";
import { ClipboardCheck, SearchCheck, Package, Database } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

const STAFF: UserRole[] = ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer"];
const QA_AND_ABOVE: UserRole[] = ["system_admin", "quality_assurance_officer"];

const CARDS = [
  { label: "Knowledge Foundation", href: "/knowledge/foundation", icon: Database, description: "Institutional knowledge coverage and data provenance across all entities", roles: STAFF },
  { label: "Knowledge Review", href: "/knowledge-review", icon: ClipboardCheck, description: "Review and approve knowledge base submissions", roles: QA_AND_ABOVE },
  { label: "Knowledge Search", href: "/knowledge-search", icon: SearchCheck, description: "Search institutional knowledge and policies", roles: STAFF },
  { label: "IKP Management", href: "/ikp-management", icon: Package, description: "Manage the Institutional Knowledge Profile", roles: QA_AND_ABOVE },
];

export default function KnowledgeWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Knowledge</h1>
        <p className="text-muted-foreground mt-1">Institutional knowledge foundation, policies, and the knowledge profile.</p>
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
