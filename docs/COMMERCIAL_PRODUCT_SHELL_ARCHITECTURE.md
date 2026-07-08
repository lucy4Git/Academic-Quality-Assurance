# Commercial Product Shell — Architecture

**Sprint:** Phase 4 Wave 1  
**Completed:** 2026-07-08  
**Scope:** UX-only — no business logic, API, or database changes

---

## Design Philosophy: Quantum Precision

AQAA's visual identity follows the **Quantum Precision** aesthetic — an AI-native enterprise design language inspired by Linear, Vercel, and ChatGPT Enterprise:

- Deep charcoal sidebar (`hsl(224 71% 7%)` light / `hsl(224 71% 3%)` dark)
- Electric blue primary (`hsl(221 83% 53%)`)
- 12px / 16px border radii
- Subtle shadows, vast whitespace
- Minimal decorative borders — structure through spacing

---

## Component Architecture

### AppShell (`src/components/layout/AppShell.tsx`)
Top-level layout wrapper. Renders: `<Sidebar>` | `<Topbar>` | `<main>` | `<CommandPalette>`. Handles:
- Auth redirect (unauthenticated → `/login`)
- Global Ctrl+K listener for command palette
- Mobile sidebar auto-close on mount (`window.innerWidth < 768`)

### Sidebar (`src/components/layout/Sidebar.tsx`)
- Desktop: `w-[220px]` expanded / `w-[64px]` collapsed, inline in flex row
- Mobile: `fixed` positioned, `-translate-x-full` when closed, opens as overlay with `Fragment` backdrop
- `NavItem` component with RBAC filtering (role checked against `item.roles` from `NAV_SECTIONS`)
- Collapse toggle button (desktop only, `hidden md:flex`)
- User footer: avatar, name, institution, sign out

### Topbar (`src/components/layout/Topbar.tsx`)
- Height: 56px, `sticky top-0 z-20`, `backdrop-blur-sm`
- Mobile hamburger button (`md:hidden`) calls `toggleSidebar`
- Breadcrumb fills flex-1
- Right rail: search (`.topbar-search`), institution pill, AI Ready pill, bell, user dropdown
- Theme switcher via `next-themes` `setTheme`

### CommandPalette (`src/components/layout/CommandPalette.tsx`)
- Triggered by Ctrl+K or topbar search
- 5 groups: Navigate, AI Actions, Knowledge, Quality, Administration
- Each entry: LucideIcon + label + RBAC filter
- Keyboard hints footer

---

## Navigation Structure

```
NAV_SECTIONS (rbac.ts)
├── Home          → /dashboard      roles: ALL
├── Workspace     → /workspace      roles: STAFF (lecturer+)
├── Knowledge     → /knowledge      roles: STAFF
├── Quality       → /quality        roles: COORDINATOR_AND_ABOVE
└── Administration→ /administration roles: SA_ONLY
```

Route permission enforcement: `src/middleware.ts` (server-side cookie check).  
Render-time filtering: `NAV_SECTIONS.flatMap(s => s.items.filter(item => item.roles.includes(role)))`.

---

## Design Token System

All design tokens live in `src/app/globals.css` as CSS custom properties.

| Token | Light | Dark |
|-------|-------|------|
| `--background` | `220 14% 96%` | `224 71% 4%` |
| `--card` | `0 0% 100%` | `224 50% 7%` |
| `--sidebar-background` | `224 71% 7%` | `224 71% 3%` |
| `--primary` | `221 83% 53%` | `221 83% 63%` |
| `--radius` | `0.75rem` | `0.75rem` |

Component classes: `.aqaa-card`, `.workspace-card`, `.nav-item`, `.topbar-search`, `.status-pill`.

---

## Workspace Landing Pages

Each workspace uses a flat card grid with:
- Icon (9×9 rounded-xl, color-coded)
- Badge pill (10px uppercase)
- Label + description
- "Open →" hover animation

| Workspace | Cards | RBAC |
|-----------|-------|------|
| Knowledge | 6 | QA+ for acquisition/extraction/graph |
| Quality | 8 | COORDINATOR+ for audits; QA+ for policy |
| Administration | 9 | SA_ONLY |

---

## Mobile Behavior

- Sidebar defaults `sidebarOpen: false` on mount when `window.innerWidth < 768`
- Sidebar is `position: fixed` — does not take flex space on mobile
- Topbar shows `<Menu>` hamburger icon (`md:hidden`) that calls `toggleSidebar`
- `Fragment` renders an overlay backdrop div when sidebar is open on mobile
- NavItem `onClick` closes sidebar on mobile after navigation
