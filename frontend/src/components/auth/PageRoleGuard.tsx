"use client";

import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth.store";
import { getAllowedRoles } from "@/lib/rbac";
import type { UserRole } from "@/types";
import { ShieldX } from "lucide-react";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Client-side route guard rendered inside every (main) page.
 *
 * Works alongside the middleware:
 * - Middleware blocks unauthenticated requests (server-side, fast).
 * - PageRoleGuard handles the edge case where the client-side route state
 *   differs from middleware state (e.g., after client-side navigation, or
 *   during SPA transitions where the cookie role differs from cached state).
 *
 * Renders the "Access Denied" UI inline (keeping the AppShell/Sidebar
 * visible) instead of a full-page redirect, which is better UX.
 */
export function PageRoleGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  // While the auth store is hydrating, render nothing (AppShell shows skeleton)
  if (!user) return null;

  const allowed = getAllowedRoles(pathname);
  if (!allowed.includes(user.role as UserRole)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="rounded-full bg-destructive/10 p-6 mb-6">
          <ShieldX className="h-12 w-12 text-destructive" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Access Denied
        </h1>
        <p className="text-muted-foreground max-w-md mb-8">
          Your role (<strong>{user.role.replace(/_/g, " ")}</strong>) does not
          have permission to view this page. Contact your system administrator
          if you believe this is an error.
        </p>
        <div className="flex gap-3">
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ variant: "default" }))}
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
