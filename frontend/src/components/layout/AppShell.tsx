"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";
import { useAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/store/auth.store";
import { useUIStore } from "@/store/ui.store";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { sidebarOpen, toggleCommandPalette, setSidebarOpen } = useUIStore();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isGeneric = user?.role === "generic_user";

  // Close sidebar on mobile by default
  useEffect(() => {
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, [setSidebarOpen]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  // Global ⌘K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        toggleCommandPalette();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [toggleCommandPalette]);

  if (isLoading) {
    return (
      <div className="flex h-screen bg-background overflow-hidden">
        {/* Sidebar skeleton */}
        <div className="w-[220px] border-r border-border/60 flex flex-col gap-0 bg-sidebar flex-shrink-0">
          <div className="h-14 border-b border-sidebar-border px-4 flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-sidebar-accent animate-pulse" />
            <div className="h-3.5 w-16 rounded bg-sidebar-accent/60 animate-pulse" />
          </div>
          <div className="flex-1 p-3 space-y-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 rounded-lg bg-sidebar-accent/40 animate-pulse" />
            ))}
          </div>
          <div className="border-t border-sidebar-border p-3 space-y-1">
            <div className="h-10 rounded-lg bg-sidebar-accent/40 animate-pulse" />
          </div>
        </div>

        {/* Content skeleton */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="h-14 border-b border-border/60 px-4 flex items-center gap-3">
            <div className="h-4 w-32 rounded bg-muted animate-pulse" />
            <div className="flex-1" />
            <div className="h-9 w-44 rounded-lg bg-muted animate-pulse" />
            <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
          </div>
          <div className="flex-1 p-8 space-y-6">
            <div className="h-10 w-64 rounded-lg bg-muted animate-pulse" />
            <div className="grid grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-28 rounded-2xl bg-muted animate-pulse" />
              ))}
            </div>
            <div className="h-64 rounded-2xl bg-muted animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-background relative">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <main
          id="main-content"
          className={cn("flex-1 overflow-y-auto focus:outline-none")}
          tabIndex={-1}
        >
          <div className={cn(isGeneric ? "h-full" : "max-w-[1440px] mx-auto px-6 py-8")}>
            {children}
          </div>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
