# AQAA Changelog

All notable changes to this project are documented here.

---

## [4.0.0] — 2026-07-08 · Phase 4 Wave 1: Commercial Product Shell

### Added
- **Quantum Precision design system** — new CSS custom properties (`--sidebar-background`, `--sidebar-foreground`, `--sidebar-border`), component classes (`.aqaa-card`, `.nav-item`, `.topbar-search`, `.status-pill`), 0.75rem radius, gradient-mesh utility
- **5-workspace navigation** — Home, Workspace, Knowledge, Quality, Administration with RBAC filtering and active-state indicator
- **Sidebar** — 220px expanded / 64px collapsed, collapse toggle button, AQAA brand mark, user footer with avatar, mobile overlay + backdrop, hamburger toggle in topbar
- **Topbar** — 56px sticky, premium search button (⌘K), institution status pill, AI Ready pill, notification bell, theme switcher dropdown, user avatar dropdown
- **Home page** (`DashboardView`) — Ask AQAA composer, quick actions grid, health score tile, 4 live stat tiles, Recent AI Activity feed, Today's Priorities, Continue Working cards
- **Workspace page** (`WorkspaceLandingView`) — ChatGPT-style hero, centered Ask AQAA composer, 6 suggested prompts, 4 AI Tools cards, Recent Conversations list, Pinned Documents panel
- **Knowledge landing page** — 6 cards: Foundation, Public Acquisition, Extraction Review, Semantic Search, Knowledge Graph, Documents
- **Quality landing page** — 8 cards: Audits, Evidence, Upload Evidence, Findings, Compliance, Accreditation, Programme Review, Policy Review
- **Administration landing page** — 9 cards (SA-only): Institutions, Users, Roles, Permissions, AI Providers, Monitoring, Scheduler, Logs, Settings
- **Enhanced Command Palette** — 5 grouped sections (Navigate, AI Actions, Knowledge, Quality, Administration) with RBAC filtering and keyboard hints
- **Mobile responsive layout** — sidebar defaults closed on mobile, hamburger in topbar, overlay backdrop, nav items close sidebar on tap

### Changed
- `globals.css` — complete rewrite to Quantum Precision design tokens (light + dark modes)
- `rbac.ts` — NAV_SECTIONS reduced to 5 items; `/workspace` route added to ROUTE_PERMISSIONS
- `Sidebar.tsx` — full redesign (dark, minimal, RBAC-filtered)
- `Topbar.tsx` — full redesign (sticky, search, pills, dropdown)
- `AppShell.tsx` — removed FloatingAIButton; added mobile sidebar close on mount
- `CommandPalette.tsx` — full redesign with grouped sections
- `Breadcrumb.tsx` — added segment labels for all 5 workspace routes
- `dashboard/page.tsx` — now delegates to `DashboardView`

### Removed
- `FloatingAIButton` — replaced by Ask AQAA in Home and Workspace pages (component stub returns null)

### Security
- No authentication, RBAC, tenant isolation, or API changes — UX-only sprint

---

## [3.x.x] — Prior Releases

See git log for Phase 1–3 history: `git log --oneline`
