"use client";

import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

interface RoleGuardProps {
  /** Roles that are allowed to render the children */
  roles: UserRole[];
  children: React.ReactNode;
  /** Optional element to render when the role check fails */
  fallback?: React.ReactNode;
}

/**
 * Renders `children` only when the current user's role is in `roles`.
 * Renders `fallback` (default: null) otherwise.
 *
 * This is a client-side UI guard. Server-side protection is handled by
 * middleware.ts and API-level role checks in the FastAPI backend.
 */
export function RoleGuard({ roles, children, fallback = null }: RoleGuardProps) {
  const user = useAuthStore((s) => s.user);

  if (!user) return null;
  if (!roles.includes(user.role)) return <>{fallback}</>;

  return <>{children}</>;
}

/**
 * Renders `children` only when the role check FAILS (inverse of RoleGuard).
 * Useful for hiding elements from privileged roles, e.g. showing a
 * "read-only" notice to students.
 */
export function ExcludeRole({
  roles,
  children,
}: {
  roles: UserRole[];
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;
  if (roles.includes(user.role)) return null;
  return <>{children}</>;
}
