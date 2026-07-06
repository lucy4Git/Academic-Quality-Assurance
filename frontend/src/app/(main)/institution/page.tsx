"use client";

import Link from "next/link";
import { Building2, GraduationCap, BookOpen, Layers, Boxes } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

const CARDS = [
  { label: "Institutions", href: "/institutions", icon: Building2, description: "Manage institution profiles and settings", roles: ["system_admin", "quality_assurance_officer"] as UserRole[] },
  { label: "Faculties", href: "/faculties", icon: GraduationCap, description: "Faculty structure and leadership", roles: ["system_admin", "quality_assurance_officer", "faculty_dean"] as UserRole[] },
  { label: "Departments", href: "/departments", icon: BookOpen, description: "Department management and HOD assignment", roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department"] as UserRole[] },
  { label: "Programmes", href: "/programmes", icon: Layers, description: "Programme catalogue and accreditation", roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer", "student"] as UserRole[] },
  { label: "Modules", href: "/modules", icon: Boxes, description: "Module delivery and compliance tracking", roles: ["system_admin", "quality_assurance_officer", "faculty_dean", "head_of_department", "programme_coordinator", "lecturer", "student"] as UserRole[] },
];

export default function InstitutionWorkspacePage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;
  const visible = CARDS.filter((c) => !role || c.roles.includes(role));
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Institution</h1>
        <p className="text-muted-foreground mt-1">Manage your institutional hierarchy and organisational structure.</p>
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
