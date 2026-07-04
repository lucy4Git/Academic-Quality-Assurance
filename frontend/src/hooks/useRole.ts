"use client";

import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

/**
 * Exposes granular role-check helpers derived from the auth store.
 * Import this hook in components to show/hide UI based on role.
 */
export function useRole() {
  const {
    user,
    hasRole,
    canTriggerAudit,
    canUpload,
    canResolveFindings,
    isAdmin,
    isQAOfficer,
  } = useAuthStore();

  return {
    role: user?.role as UserRole | undefined,

    // Cumulative hierarchy checks (mirrors backend require_roles shortcuts)
    isSysAdmin: hasRole("system_admin"),
    isQAOfficer: isQAOfficer(),
    isDean: hasRole("system_admin", "quality_assurance_officer", "faculty_dean"),
    isHOD: hasRole(
      "system_admin",
      "quality_assurance_officer",
      "faculty_dean",
      "head_of_department"
    ),
    isCoordinator: hasRole(
      "system_admin",
      "quality_assurance_officer",
      "faculty_dean",
      "head_of_department",
      "programme_coordinator"
    ),
    isLecturer: hasRole(
      "system_admin",
      "quality_assurance_officer",
      "faculty_dean",
      "head_of_department",
      "programme_coordinator",
      "lecturer"
    ),
    isStudent: hasRole("student"),

    // Feature-level permissions
    canTriggerAudit: canTriggerAudit(),
    canUpload: canUpload(),
    canResolveFindings: canResolveFindings(),
    isAdmin: isAdmin(),

    // Generic role membership check
    hasRole,
  };
}
