"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen, Bell, Sun, Moon, Monitor, Search, Zap, LogOut, User } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Breadcrumb } from "./Breadcrumb";
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import { useAuth } from "@/hooks/useAuth";
import { useUnreadCount } from "@/hooks/useWorkspace";
import { useInstitutions } from "@/hooks/useInstitutions";
import { ROLE_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { UserRole } from "@/types";

function InstitutionBadge({ code }: { code?: string }) {
  if (!code) {
    return (
      <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
        AQAA Platform
      </span>
    );
  }
  const isTUT = code === "TUT";
  return (
    <span className={cn(
      "hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border",
      isTUT
        ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-800"
        : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 border-red-200 dark:border-red-800"
    )}>
      <span className={cn("h-1.5 w-1.5 rounded-full flex-shrink-0", isTUT ? "bg-blue-500" : "bg-red-600")} />
      {code}
    </span>
  );
}

export function Topbar() {
  const { sidebarOpen, toggleSidebar, toggleCommandPalette } = useUIStore();
  const { setTheme } = useTheme();
  const { logout } = useAuth();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.unread ?? 0;
  const { data: institutions } = useInstitutions();
  const userInstitution = institutions?.find((i) => i.id === user?.institution_id);
  const isSystemAdmin = user?.role === "system_admin";
  const role = user?.role as UserRole | undefined;

  const initials = user?.full_name
    ? user.full_name.split(" ").slice(0, 2).map((n) => n[0]).join("").toUpperCase()
    : "?";

  return (
    <header className="flex items-center gap-2 h-12 px-3 border-b bg-background border-border flex-shrink-0">
      {/* Sidebar toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:text-foreground flex-shrink-0"
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {sidebarOpen ? (
          <PanelLeftClose className="h-4 w-4" />
        ) : (
          <PanelLeftOpen className="h-4 w-4" />
        )}
      </Button>

      {/* Breadcrumb */}
      <div className="flex-1 min-w-0">
        <Breadcrumb />
      </div>

      {/* Utility rail */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* Search / command palette — desktop */}
        <button
          type="button"
          onClick={toggleCommandPalette}
          className="hidden md:flex items-center gap-2 h-8 px-3 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border/60"
          aria-label="Open command palette"
        >
          <Search className="h-3.5 w-3.5 flex-shrink-0" />
          <span>Search…</span>
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-80">
            ⌘K
          </kbd>
        </button>
        {/* Search — mobile icon only */}
        <button
          type="button"
          onClick={toggleCommandPalette}
          className="md:hidden flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="Search"
        >
          <Search className="h-4 w-4" />
        </button>

        {/* Institution context badge */}
        <InstitutionBadge code={isSystemAdmin ? undefined : userInstitution?.code} />

        {/* AI status badge */}
        <span className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <Zap className="h-3 w-3 flex-shrink-0" />
          AI Ready
        </span>

        {/* Notification bell */}
        <Link
          href="/notifications"
          className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white leading-none">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Link>

        {/* User avatar + dropdown menu */}
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Avatar className="h-8 w-8 cursor-pointer">
              <AvatarFallback className="bg-primary text-white text-xs font-medium">
                {initials}
              </AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="px-2 py-2 border-b border-border mb-1">
              <p className="text-sm font-semibold text-foreground truncate">{user?.full_name ?? "User"}</p>
              <p className="text-xs text-muted-foreground truncate">{role ? ROLE_LABELS[role] : ""}</p>
            </div>
            <DropdownMenuItem onClick={() => setTheme("light")}>
              <Sun className="mr-2 h-4 w-4" />
              Light Mode
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("dark")}>
              <Moon className="mr-2 h-4 w-4" />
              Dark Mode
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("system")}>
              <Monitor className="mr-2 h-4 w-4" />
              System Theme
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push("/settings/profile")}>
              <User className="mr-2 h-4 w-4" />
              View Profile
            </DropdownMenuItem>
            <DropdownMenuItem variant="destructive" onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
