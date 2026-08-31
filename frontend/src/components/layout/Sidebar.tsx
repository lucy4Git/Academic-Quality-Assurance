"use client";

import { Fragment } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  LayoutGrid,
  Library,
  BookOpen,
  ShieldCheck,
  Settings2,
  Search,
  Files,
  Bookmark,
  Clock3,
  MessageSquarePlus,
  LogOut,
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getNavSections } from "@/lib/rbac";
import { ROLE_LABELS } from "@/lib/constants";
import { useInstitutions } from "@/hooks/useInstitutions";
import type { UserRole } from "@/types";

const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  LayoutGrid,
  Library,
  BookOpen,
  ShieldCheck,
  Settings2,
  Search,
  Files,
  Bookmark,
  Clock3,
  MessageSquarePlus,
};

function NavItem({
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
  const { setSidebarOpen } = useUIStore();
  const isActive =
    pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
  const Icon = ICON_MAP[icon] ?? Home;

  return (
    <Link
      href={href}
      title={collapsed ? label : undefined}
      aria-current={isActive ? "page" : undefined}
      onClick={() => {
        if (window.innerWidth < 768) setSidebarOpen(false);
      }}
      className={cn(
        "nav-item group select-none",
        isActive && "active",
        collapsed && "justify-center px-0"
      )}
    >
      <Icon
        className={cn(
          "flex-shrink-0 transition-colors",
          collapsed ? "h-5 w-5" : "h-4 w-4",
          isActive
            ? "text-sidebar-foreground"
            : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground"
        )}
        aria-hidden="true"
      />
      {!collapsed && (
        <span className="truncate text-[13.5px]">{label}</span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { logout } = useAuth();
  const user = useAuthStore((s) => s.user);
  const collapsed = !sidebarOpen;
  const role = user?.role as UserRole | undefined;
  const isSystemAdmin = role === "system_admin";

  const { data: institutions } = useInstitutions();
  const userInstitution = institutions?.find((i) => i.id === user?.institution_id);

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .slice(0, 2)
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "?";

  const navSections = getNavSections(role);
  const visibleItems = navSections.flatMap((s) =>
    s.items.filter((item) => !role || item.roles.includes(role))
  );

  return (
    <Fragment>
      {/* Mobile backdrop */}
      {!collapsed && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "sidebar-transition flex flex-col bg-sidebar border-r border-sidebar-border relative flex-shrink-0 z-40",
          "fixed inset-y-0 left-0 h-full md:relative md:inset-auto md:h-full",
          collapsed
            ? "md:w-[64px] w-[220px] -translate-x-full md:translate-x-0"
            : "w-[220px] translate-x-0"
        )}
        aria-label="Main navigation"
      >
        {/* Brand mark */}
        <div
          className={cn(
            "flex items-center gap-2.5 min-h-[56px] border-b border-sidebar-border px-4",
            collapsed && "md:justify-center md:px-0"
          )}
        >
          <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
            <span className="text-white font-bold text-[11px] tracking-tight">AQ</span>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sidebar-foreground font-semibold text-sm tracking-tight truncate">
                AQAA
              </p>
              <p className="text-sidebar-foreground/30 text-[10px] truncate">
                Evidence workspace
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav
          className={cn(
            "flex-1 overflow-y-auto py-3 space-y-0.5",
            collapsed ? "md:px-2 px-3" : "px-3"
          )}
          aria-label="Primary navigation"
        >
          {visibleItems.map((item) => (
            <NavItem
              key={item.href}
              label={item.label}
              href={item.href}
              icon={item.icon}
              collapsed={collapsed}
            />
          ))}
        </nav>

        {/* Collapse toggle (desktop only) */}
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "hidden md:flex absolute -right-3 top-[72px] z-10",
            "h-6 w-6 items-center justify-center rounded-full",
            "bg-sidebar border border-sidebar-border",
            "text-sidebar-foreground/50 hover:text-sidebar-foreground",
            "transition-all duration-150 hover:scale-110",
            "shadow-sm"
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-3 w-3" />
          ) : (
            <ChevronLeft className="h-3 w-3" />
          )}
        </button>

        {/* User footer */}
        <div className={cn("border-t border-sidebar-border", collapsed ? "md:p-2 p-3 space-y-1" : "p-3 space-y-1")}>
          <div
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-2 py-2",
              collapsed && "md:justify-center md:px-0"
            )}
            title={collapsed ? (user?.full_name ?? "User") : undefined}
          >
            <Avatar className="h-7 w-7 flex-shrink-0">
              <AvatarFallback className="bg-primary text-white text-[10px] font-semibold">
                {initials}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="text-[12.5px] font-medium text-sidebar-foreground truncate leading-tight">
                  {user?.full_name ?? "User"}
                </p>
                <p className="text-[10.5px] text-sidebar-foreground/40 truncate leading-tight mt-0.5">
                  {role === "generic_user" && user?.persona
                    ? user.persona === "quality_assurance_officer"
                      ? "Quality Assurance Officer"
                      : user.persona === "lecturer"
                      ? "Lecturer"
                      : "User"
                    : isSystemAdmin
                    ? "All Institutions"
                    : userInstitution
                    ? `${userInstitution.code}`
                    : role
                    ? ROLE_LABELS[role]
                    : ""}
                </p>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={logout}
            title="Sign out"
            className={cn(
              "w-full flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-[12.5px]",
              "text-sidebar-foreground/40 hover:text-destructive/80 hover:bg-destructive/10",
              "transition-colors cursor-pointer",
              collapsed && "md:justify-center md:px-0"
            )}
          >
            <LogOut className="h-3.5 w-3.5 flex-shrink-0" />
            {!collapsed && <span>Sign out</span>}
          </button>

        </div>
      </aside>
    </Fragment>
  );
}
