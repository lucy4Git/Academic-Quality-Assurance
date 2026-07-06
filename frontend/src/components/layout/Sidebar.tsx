"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  LayoutDashboard,
  Building2,
  GraduationCap,
  BookOpen,
  Users,
  Layers,
  Boxes,
  Upload,
  SearchCheck,
  AlertTriangle,
  BarChart2,
  Shield,
  Settings,
  LogOut,
  ChevronRight,
  Library,
  GitBranch,
  ShieldCheck,
  CalendarDays,
  Bell,
  ClipboardCheck,
  BrainCircuit,
  Brain,
  FileBarChart,
  Package,
  Calculator,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useUIStore } from "@/store/ui.store";
import { ROLE_LABELS } from "@/lib/constants";
import { useAuthStore } from "@/store/auth.store";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { NAV_SECTIONS } from "@/lib/rbac";
import type { UserRole } from "@/types";
import { useInstitutions } from "@/hooks/useInstitutions";

// Map icon name strings → lucide components
const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  LayoutDashboard,
  Building2,
  GraduationCap,
  BookOpen,
  Users,
  Layers,
  Boxes,
  Upload,
  SearchCheck,
  AlertTriangle,
  BarChart2,
  Shield,
  Settings,
  Library,
  GitBranch,
  ShieldCheck,
  CalendarDays,
  Bell,
  ClipboardCheck,
  BrainCircuit,
  Brain,
  FileBarChart,
  Package,
  Calculator,
};

function NavItemRow({
  label,
  href,
  icon,
  collapsed,
}: {
  label: string;
  href: string;
  icon: string;
  collapsed: boolean;
}) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);
  const Icon = ICON_MAP[icon] ?? LayoutDashboard;

  return (
    <Link
      href={href}
      title={collapsed ? label : undefined}
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150",
        "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent",
        isActive && "bg-sidebar-accent text-sidebar-foreground font-medium"
      )}
    >
      <Icon className={cn("flex-shrink-0", collapsed ? "h-5 w-5" : "h-4 w-4")} />
      {!collapsed && <span className="truncate">{label}</span>}
      {!collapsed && isActive && (
        <ChevronRight className="ml-auto h-3 w-3 opacity-60" />
      )}
    </Link>
  );
}

export function Sidebar() {
  const { sidebarOpen } = useUIStore();
  const { logout } = useAuth();
  const user = useAuthStore((s) => s.user);
  const collapsed = !sidebarOpen;
  const role = user?.role as UserRole | undefined;
  const isSystemAdmin = role === "system_admin";

  // Fetch institution list so we can display the user's institution name
  const { data: institutions } = useInstitutions();
  const userInstitution = institutions?.find(
    (i) => i.id === user?.institution_id
  );

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .slice(0, 2)
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "?";

  // Filter sections and items to only those the current role can access
  const visibleSections = NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter(
      (item) => !role || item.roles.includes(role)
    ),
  })).filter((section) => section.items.length > 0);

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-200",
        collapsed ? "w-16" : "w-64"
      )}
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div
        className={cn(
          "flex items-center gap-3 px-4 py-4 border-b border-sidebar-border min-h-[64px]",
          collapsed && "justify-center px-2"
        )}
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
          <span className="text-white font-bold text-sm">AQ</span>
        </div>
        {!collapsed && (
          <p className="text-sidebar-foreground font-semibold text-sm truncate">
            AQAA
          </p>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {visibleSections.map((section, idx) => (
          <div key={idx}>
            {section.title && !collapsed && (
              <p className="px-3 pt-4 pb-1 text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/40">
                {section.title}
              </p>
            )}
            {section.title && collapsed && idx > 0 && (
              <Separator className="my-2 bg-sidebar-border" />
            )}
            {section.items.map((item) => (
              <NavItemRow
                key={item.href}
                label={item.label}
                href={item.href}
                icon={item.icon}
                collapsed={collapsed}
              />
            ))}
          </div>
        ))}
      </nav>

      {/* User footer — always visible, no dropdown */}
      <div className="border-t border-sidebar-border p-3 space-y-1">
        <div
          className={cn(
            "flex items-center gap-3 px-2 py-1",
            collapsed && "justify-center"
          )}
        >
          <Avatar className="h-8 w-8 flex-shrink-0">
            <AvatarFallback className="bg-primary text-white text-xs font-medium">
              {initials}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {user?.full_name ?? "User"}
              </p>
              <p className="text-xs text-sidebar-foreground/50 truncate">
                {role ? ROLE_LABELS[role] : ""}
              </p>
              {/* Institution context line */}
              {isSystemAdmin ? (
                <p className="text-[10px] text-blue-400/80 font-medium truncate mt-0.5">
                  All Institutions
                </p>
              ) : userInstitution ? (
                <p className="text-[10px] text-sidebar-foreground/40 truncate mt-0.5">
                  {userInstitution.code}
                  {userInstitution.institution_type === "pilot" && (
                    <span className="ml-1 text-blue-400/70">· Pilot</span>
                  )}
                </p>
              ) : null}
            </div>
          )}
        </div>

        {/* Logout — always visible */}
        <button
          type="button"
          onClick={logout}
          title="Sign out"
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm",
            "text-destructive/80 hover:text-destructive hover:bg-destructive/10",
            "transition-colors cursor-pointer",
            collapsed && "justify-center"
          )}
        >
          <LogOut className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span className="font-medium">Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
