"use client";

import Link from "next/link";
import { Users, Settings, Brain } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

const SA_ONLY: UserRole[] = ["system_admin"];

const CARDS = [
  { label: "Users", href: "/users", icon: Users, description: "User accounts, roles, and access management", roles: SA_ONLY },
  { label: "System Settings", href: "/settings/system", icon: Settings, description: "Platform configuration and feature flags", roles: SA_ONLY },
  { label: "AI Providers", href: "/settings/ai-providers", icon: Brain, description: "AI provider configuration and health monitoring", roles: SA_ONLY },
];

export default function AdministrationWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Administration</h1>
        <p className="text-muted-foreground mt-1">Platform administration, users, and system configuration.</p>
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
