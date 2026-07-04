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
];

const STAFF: UserRole[] = [
  "system_admin",
  "quality_assurance_officer",
  "faculty_dean",
  "head_of_department",
  "programme_coordinator",
  "lecturer",
];

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
  "/dashboard":           ALL,
  "/settings/profile":    ALL,
  "/settings/security":   ALL,
  "/settings/notifications": ALL,

  // ── Institution hierarchy ─────────────────────────────────────────────────
  "/institutions":        QA_AND_ABOVE,       // create/edit/delete gated inside component
  "/faculties":           DEAN_AND_ABOVE,
  "/departments":         HOD_AND_ABOVE,
  "/programmes":          ALL,                // students can view their own programme (read-only)
  "/modules":             ALL,                // students can view their own modules (read-only)

  // ── Knowledge Base ────────────────────────────────────────────────────────
  "/knowledge-review":    QA_AND_ABOVE,
  "/knowledge-search":    STAFF,
  "/ikp-management":      QA_AND_ABOVE,

  // ── Quality / Evidence / Audit ────────────────────────────────────────────
  "/files":               STAFF,
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

  // ── Administration (SA only) ───────────────────────────────────────────────
  "/users":               SA_ONLY,
  "/settings/system":     SA_ONLY,
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

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "",
    items: [
      { label: "Dashboard",       href: "/dashboard",        icon: "LayoutDashboard", roles: ALL },
    ],
  },
  {
    title: "INSTITUTION",
    items: [
      { label: "Institutions",    href: "/institutions",     icon: "Building2",      roles: QA_AND_ABOVE },
      { label: "Faculties",       href: "/faculties",        icon: "GraduationCap",  roles: DEAN_AND_ABOVE },
      { label: "Departments",     href: "/departments",      icon: "BookOpen",       roles: HOD_AND_ABOVE },
      { label: "Programmes",      href: "/programmes",       icon: "Layers",         roles: ALL },
      { label: "Modules",         href: "/modules",          icon: "Boxes",          roles: ALL },
    ],
  },
  {
    title: "KNOWLEDGE",
    items: [
      { label: "Knowledge Review",  href: "/knowledge-review",  icon: "ClipboardCheck", roles: QA_AND_ABOVE },
      { label: "Knowledge Search",  href: "/knowledge-search",  icon: "SearchCheck",    roles: STAFF },
      { label: "IKP Management",    href: "/ikp-management",    icon: "Package",        roles: QA_AND_ABOVE },
    ],
  },
  {
    title: "QUALITY",
    items: [
      { label: "File Library",    href: "/files",            icon: "Library",        roles: STAFF },
      { label: "Upload Evidence", href: "/files/upload",     icon: "Upload",         roles: STAFF },
      { label: "Audit Centre",    href: "/audits",           icon: "SearchCheck",    roles: COORDINATOR_AND_ABOVE },
      { label: "Findings",        href: "/findings",         icon: "AlertTriangle",  roles: STAFF },
    ],
  },
  {
    title: "WORKFLOW",
    items: [
      { label: "Workflow",        href: "/workflow",         icon: "GitBranch",      roles: COORDINATOR_AND_ABOVE },
      { label: "Approvals",       href: "/approvals",        icon: "ShieldCheck",    roles: QA_AND_ABOVE },
      { label: "Calendar",        href: "/calendar",         icon: "CalendarDays",   roles: COORDINATOR_AND_ABOVE },
      { label: "Notifications",   href: "/notifications",    icon: "Bell",           roles: STAFF },
    ],
  },
  {
    title: "AI ASSISTANT",
    items: [
      { label: "AI Workspace",             href: "/ai-workspace",              icon: "Brain",        roles: STAFF },
      { label: "AI QA Assistant",          href: "/ai-assistant",              icon: "BrainCircuit", roles: STAFF },
      { label: "Qualification Intelligence", href: "/qualification-intelligence", icon: "Calculator",   roles: STAFF },
      { label: "Institution Workspace",    href: "/workspace",                 icon: "Building2",    roles: STAFF },
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      { label: "Analytics",       href: "/analytics",         icon: "BarChart2",      roles: HOD_AND_ABOVE },
      { label: "Reports",         href: "/reports",           icon: "FileBarChart",   roles: HOD_AND_ABOVE },
      { label: "Accreditation",   href: "/accreditation",    icon: "Shield",         roles: DEAN_AND_ABOVE },
    ],
  },
  {
    title: "ADMINISTRATION",
    items: [
      { label: "Users",           href: "/users",            icon: "Users",          roles: SA_ONLY },
      { label: "Settings",        href: "/settings/system",  icon: "Settings",       roles: SA_ONLY },
    ],
  },
];
