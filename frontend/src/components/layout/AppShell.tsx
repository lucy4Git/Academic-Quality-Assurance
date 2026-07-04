"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useAuth } from "@/hooks/useAuth";
import { Skeleton } from "@/components/ui/skeleton";
import { useUIStore } from "@/store/ui.store";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * Authenticated shell layout.
 * Renders sidebar (fixed left) + topbar + scrollable content area.
 * Handles session rehydration and redirects unauthenticated users.
 */
export function AppShell({ children }: AppShellProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const { sidebarOpen } = useUIStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Show a minimal loading skeleton while session rehydrates
  if (isLoading) {
    return (
      <div className="flex h-screen bg-background">
        {/* Sidebar skeleton */}
        <div className="w-64 border-r border-border flex flex-col gap-3 p-4 bg-sidebar">
          <Skeleton className="h-10 w-full rounded-lg bg-sidebar-accent" />
          <div className="space-y-2 pt-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full rounded-lg bg-sidebar-accent" />
            ))}
          </div>
        </div>
        {/* Main content skeleton */}
        <div className="flex-1 flex flex-col">
          <div className="h-12 border-b border-border px-4 flex items-center gap-3">
            <Skeleton className="h-5 w-48" />
          </div>
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-24 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-64 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Fixed sidebar */}
      <Sidebar />

      {/* Main area: topbar + scrollable content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <main
          id="main-content"
          className={cn(
            "flex-1 overflow-y-auto",
            "focus:outline-none"
          )}
          tabIndex={-1}
        >
          <div className="max-w-[1440px] mx-auto p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
