/**
 * AQAA Frontend RBAC — single source of truth.
 *
 * Every protected route is listed here with the roles that may access it.
 * The middleware, Sidebar, and PageRoleGuard all derive their rules from
 * this file so permissions can never diverge between layers.
 *
 * Role hierarchy (cumulative — each role inherits all permissions below):
 *   system_admin
 *     └─ quality_assurance_officer
 *          └─ faculty_dean
 *               └─ head_of_department
 *                    └─ programme_coordinator
 *                         └─ lecturer
 *                              └─ student
 */

import type { UserRole } from "@/types";

// Convenient role arrays used across multiple rules
const ALL: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
  "lecturer",
  "student",
  "generic_user",
];

const STAFF: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
  "lecturer",
];

const GENERIC_STAFF: UserRole[] = ["generic_user"];

const QA_AND_ABOVE: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
];

const DEAN_AND_ABOVE: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
];

const HOD_AND_ABOVE: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
];

const COORDINATOR_AND_ABOVE: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
];

const SA_ONLY: UserRole[] = ["system_admin"];

const GENERIC_ONLY: UserRole[] = ["generic_user"];

/**
 * Route permission map.
 *
 * Keys are path PREFIXES — a role is allowed on `/institutions/abc/edit`
 * if it is allowed on `/institutions`.
 *
 * Order does not matter; the lookup function uses the LONGEST matching prefix.
 */
export const ROUTE_PERMISSIONS: Record<string, UserRole[]> = {
  // ── Always accessible (authenticated) ────────────────────────────────────
  "/dashboard":           [...STAFF, "student"],
  "/settings/profile":    ALL,
  "/settings/security":   ALL,
  "/settings/notifications": ALL,

  // ── Generic user (conversation-first workspace) ──────────────────────────
  "/workspace":           [...STAFF, "student", "generic_user"],
  "/onboarding":          ALL,

  // ── Institution hierarchy ─────────────────────────────────────────────────
  "/institutions":        QA_AND_ABOVE,       // create/edit/delete gated inside component
  "/faculties":           DEAN_AND_ABOVE,
  "/departments":         HOD_AND_ABOVE,
  "/programmes":          [...STAFF, "student"],                // students can view their own programme (read-only)
  "/modules":             [...STAFF, "student"],                // students can view their own modules (read-only)

  // ── Knowledge Base ────────────────────────────────────────────────────────
  "/knowledge-review":    QA_AND_ABOVE,
  "/knowledge-search":    STAFF,
  "/ikp-management":      QA_AND_ABOVE,
  "/knowledge/foundation": STAFF,
  "/knowledge/acquisition": QA_AND_ABOVE,
  "/institution/profile":  STAFF,

  // ── Library ───────────────────────────────────────────────────────────────
  "/library":             [...STAFF, "generic_user"],

  // ── Quality / Evidence / Audit ────────────────────────────────────────────
  "/files":               [...STAFF, "generic_user"],
  "/audits":              COORDINATOR_AND_ABOVE,
  "/findings":            STAFF,

  // ── Workflow / Collaboration ───────────────────────────────────────────────
  "/workflow":            COORDINATOR_AND_ABOVE,
  "/approvals":           QA_AND_ABOVE,
  "/calendar":            COORDINATOR_AND_ABOVE,
  "/notifications":       STAFF,

  // ── AI Assistant ─────────────────────────────────────────────────────────
  "/ai-assistant":        STAFF,

  // ── Qualification Intelligence ────────────────────────────────────────────
  "/qualification-intelligence": STAFF,

  // ── Analytics ─────────────────────────────────────────────────────────────
  "/analytics":           HOD_AND_ABOVE,
  "/reports":             HOD_AND_ABOVE,
  "/accreditation":       DEAN_AND_ABOVE,

  // ── Primary workspace landing pages ───────────────────────────────────────
  "/institution":         QA_AND_ABOVE,
  "/quality":             COORDINATOR_AND_ABOVE,
  "/knowledge":           STAFF,
  "/ai":                  STAFF,
  "/administration":      SA_ONLY,

  // ── Administration (SA only) ───────────────────────────────────────────────
  "/users":               SA_ONLY,
  "/settings/system":     SA_ONLY,
  "/settings/ai-providers": SA_ONLY,          // AI provider monitoring — sysadmin only
  "/settings":            SA_ONLY,            // root /settings → SA; sub-paths checked separately
};

/**
 * Return the set of roles allowed on `pathname`.
 * Uses the LONGEST matching prefix so `/settings/profile` beats `/settings`.
 * Returns `ALL` if no rule matches (open to any authenticated user).
 */
export function getAllowedRoles(pathname: string): UserRole[] {
  let bestKey = "";
  let bestRoles: UserRole[] = ALL;

  for (const [prefix, roles] of Object.entries(ROUTE_PERMISSIONS)) {
    if (
      (pathname === prefix || pathname.startsWith(prefix + "/")) &&
      prefix.length > bestKey.length
    ) {
      bestKey = prefix;
      bestRoles = roles;
    }
  }

  return bestRoles;
}

/**
 * Return true when `role` is allowed to access `pathname`.
 */
export function canAccess(pathname: string, role: UserRole): boolean {
  return getAllowedRoles(pathname).includes(role);
}

// ── Sidebar nav definition ──────────────────────────────────────────────────
// Each item declares which roles may SEE the link in the sidebar.
// Actual page access is enforced separately by getAllowedRoles.

export interface NavItem {
  label: string;
  href: string;
  icon: string;           // lucide icon name resolved in Sidebar component
  roles: UserRole[];
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

/**
 * Primary navigation — Generic user conversation-first shell.
 * Generic users see only: New conversation → Search → Library → Files → Saved outputs → Recent
 * Institutional users see traditional 5-workspace layout.
 */
export const GENERIC_NAV_SECTIONS: NavSection[] = [
  {
    title: "",
    items: [
      { label: "New conversation", href: "/workspace",     icon: "LayoutGrid",    roles: GENERIC_ONLY },
      { label: "Search",           href: "/search",        icon: "Library",       roles: GENERIC_ONLY },
      { label: "Library",          href: "/library",       icon: "BookOpen",      roles: GENERIC_ONLY },
      { label: "Files",            href: "/files",         icon: "ShieldCheck",   roles: GENERIC_ONLY },
      { label: "Saved outputs",    href: "/saved",         icon: "Home",          roles: GENERIC_ONLY },
      { label: "Recent",           href: "/recent",        icon: "Library",       roles: GENERIC_ONLY },
    ],
  },
];

export const INSTITUTIONAL_NAV_SECTIONS: NavSection[] = [
  {
    title: "",
    items: [
      { label: "Home",           href: "/dashboard",      icon: "Home",          roles: STAFF },
      { label: "Workspace",      href: "/workspace",      icon: "LayoutGrid",    roles: STAFF },
      { label: "Library",        href: "/library",        icon: "Library",       roles: STAFF },
      { label: "Knowledge",      href: "/knowledge",      icon: "BookOpen",      roles: STAFF },
      { label: "Quality",        href: "/quality",        icon: "ShieldCheck",   roles: COORDINATOR_AND_ABOVE },
      { label: "Administration", href: "/administration", icon: "Settings2",     roles: SA_ONLY },
    ],
  },
];

export const NAV_SECTIONS: NavSection[] = INSTITUTIONAL_NAV_SECTIONS;

export function getNavSections(role?: UserRole): NavSection[] {
  if (role === "generic_user") return GENERIC_NAV_SECTIONS;
  return INSTITUTIONAL_NAV_SECTIONS;
}
