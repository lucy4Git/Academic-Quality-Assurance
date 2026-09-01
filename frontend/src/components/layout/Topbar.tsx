"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  Sun,
  Moon,
  Monitor,
  Search,
  Zap,
  LogOut,
  User,
  Settings,
  Menu,
  CircleHelp,
  SlidersHorizontal,
} from "lucide-react";
import { useTheme } from "next-themes";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Breadcrumb } from "./Breadcrumb";
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import { useAuth } from "@/hooks/useAuth";
import { useUnreadCount } from "@/hooks/useWorkspace";
import { useInstitutions } from "@/hooks/useInstitutions";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { ROLE_LABELS } from "@/lib/constants";
import type { UserRole } from "@/types";

export function Topbar() {
  const { toggleCommandPalette, toggleSidebar } = useUIStore();
  const { setTheme } = useTheme();
  const { logout } = useAuth();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isGeneric = user?.role === "generic_user";
  const { data: unreadData } = useUnreadCount(Boolean(user) && !isGeneric);
  const unreadCount = unreadData?.unread ?? 0;
  const { data: institutions } = useInstitutions();
  const userInstitution = institutions?.find((i) => i.id === user?.institution_id);
  const isSystemAdmin = user?.role === "system_admin";
  const role = user?.role as UserRole | undefined;

  const initials = user?.full_name
    ? user.full_name.split(" ").slice(0, 2).map((n) => n[0]).join("").toUpperCase()
    : "?";

  const institutionLabel = isSystemAdmin
    ? "AQAA Platform"
    : userInstitution?.code ?? "AQAA";

  if (isGeneric) {
    return (
      <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border/50 bg-background/90 px-3 backdrop-blur-md sm:px-4" role="banner">
        <button type="button" onClick={toggleSidebar} aria-label="Toggle navigation" className="grid h-10 w-10 place-items-center rounded-xl text-muted-foreground hover:bg-muted md:hidden"><Menu className="h-5 w-5" /></button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">AQAA conversation</p>
          <p className="truncate text-[11px] text-muted-foreground">Academic quality assurance AI</p>
        </div>
        <span className="hidden items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-800 sm:inline-flex dark:bg-emerald-950/40 dark:text-emerald-300">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" /> Evidence aware
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger aria-label="Profile menu" className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Avatar className="h-9 w-9"><AvatarFallback className="bg-primary text-xs font-semibold text-white">{initials}</AvatarFallback></Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <div className="px-2 py-2"><p className="truncate text-sm font-semibold">{user?.full_name}</p><p className="truncate text-xs text-muted-foreground">{user?.email}</p></div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push("/settings/profile")}><User className="mr-2 h-4 w-4" />Profile</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/onboarding")}><SlidersHorizontal className="mr-2 h-4 w-4" />Personalization / Work focus</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/settings")}><Settings className="mr-2 h-4 w-4" />Settings</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/help")}><CircleHelp className="mr-2 h-4 w-4" />Help</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={logout}><LogOut className="mr-2 h-4 w-4" />Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>
    );
  }

  return (
    <header
      className="flex items-center gap-3 h-14 px-4 border-b border-border/60 bg-background/95 backdrop-blur-sm flex-shrink-0 sticky top-0 z-20"
      role="banner"
    >
      {/* Mobile hamburger */}
      <button
        type="button"
        onClick={toggleSidebar}
        aria-label="Toggle navigation"
        className="md:hidden flex items-center justify-center h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
      >
        <Menu className="h-4 w-4" />
      </button>

      {/* Breadcrumb — fills remaining space */}
      <div className="flex-1 min-w-0">
        <Breadcrumb />
      </div>

      {/* Right utility rail */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* Universal search / command palette */}
        <button
          type="button"
          onClick={toggleCommandPalette}
          aria-label="Open command palette (⌘K)"
          className="topbar-search hidden md:flex min-w-[180px]"
        >
          <Search className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span className="flex-1 text-left">Search…</span>
          <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            ⌘K
          </kbd>
        </button>
        {/* Mobile search icon */}
        <button
          type="button"
          onClick={toggleCommandPalette}
          aria-label="Search"
          className="md:hidden flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
        >
          <Search className="h-4 w-4" aria-hidden="true" />
        </button>

        {/* Institution context badge */}
        <span
          className="status-pill hidden sm:inline-flex bg-primary/6 text-primary border-primary/20"
          title={isSystemAdmin ? "All Institutions" : userInstitution?.name}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" aria-hidden="true" />
          {institutionLabel}
        </span>

        {/* AI status */}
        <span className="status-pill hidden lg:inline-flex bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900">
          <Zap className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
          AI Ready
        </span>

        {/* Notifications */}
        <Link
          href="/notifications"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
          className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          {unreadCount > 0 && (
            <span
              aria-hidden="true"
              className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white leading-none"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Link>

        {/* User profile dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger
            className="flex items-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            aria-label="User menu"
          >
            <Avatar className="h-8 w-8 cursor-pointer ring-2 ring-transparent hover:ring-primary/30 transition-all">
              <AvatarFallback className="bg-primary text-white text-[11px] font-semibold">
                {initials}
              </AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" className="w-60 p-1.5">
            {/* Identity header */}
            <div className="px-2 py-2.5 mb-1">
              <p className="text-sm font-semibold text-foreground truncate">
                {user?.full_name ?? "User"}
              </p>
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {role ? ROLE_LABELS[role] : ""}
              </p>
              {isSystemAdmin ? (
                <span className="inline-flex items-center mt-1.5 gap-1 text-[10.5px] font-medium text-primary">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  All Institutions
                </span>
              ) : userInstitution ? (
                <span className="inline-flex items-center mt-1.5 gap-1 text-[10.5px] text-muted-foreground">
                  {userInstitution.name}
                </span>
              ) : null}
            </div>

            <DropdownMenuSeparator className="my-1" />

            <DropdownMenuLabel className="text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground/60 px-2 py-1">
              Appearance
            </DropdownMenuLabel>
            <DropdownMenuItem onClick={() => setTheme("light")} className="text-sm">
              <Sun className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
              Light Mode
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("dark")} className="text-sm">
              <Moon className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
              Dark Mode
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("system")} className="text-sm">
              <Monitor className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
              System Theme
            </DropdownMenuItem>

            <DropdownMenuSeparator className="my-1" />

            <DropdownMenuItem
              onClick={() => router.push("/settings/profile")}
              className="text-sm"
            >
              <User className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
              Profile Settings
            </DropdownMenuItem>
            {role === "system_admin" && (
              <DropdownMenuItem
                onClick={() => router.push("/settings/system")}
                className="text-sm"
              >
                <Settings className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
                System Settings
              </DropdownMenuItem>
            )}

            <DropdownMenuSeparator className="my-1" />

            <DropdownMenuItem
              variant="destructive"
              onClick={logout}
              className="text-sm"
            >
              <LogOut className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
