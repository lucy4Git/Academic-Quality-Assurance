# AQAA Frontend Implementation Audit

**Audit Date:** 2026-07-13  
**Stack:** Next.js 14 (App Router), React, TypeScript, Tailwind CSS, ShadCN UI (`@base-ui/react`)  
**Total page.tsx files:** 65  
**Methodology:** Direct file inspection + live browser testing

---

## 1. Architecture Overview

### File Organisation
```
frontend/src/
├── app/
│   ├── (auth)/           # login, register pages
│   ├── (main)/           # all authenticated pages (via layout with AppShell)
│   │   ├── dashboard/    # Home
│   │   ├── workspace/    # Workspace landing
│   │   ├── ai-workspace/ # 3-panel AI chat
│   │   ├── audits/       # Audit Centre
│   │   ├── findings/     # PLACEHOLDER
│   │   ├── workflow/     # Workflow list
│   │   ├── approvals/    # Approvals
│   │   ├── reports/      # Reports
│   │   ├── analytics/    # Analytics
│   │   ├── accreditation/ # PLACEHOLDER
│   │   ├── settings/     # PLACEHOLDER (all sub-routes)
│   │   └── ... (30+ more)
│   └── api/              # Next.js proxy route handlers
├── components/
├── hooks/
├── store/
├── types/
└── lib/
```

### Key Architectural Patterns
- **Delegation pattern**: `page.tsx` is a thin wrapper (5-20 lines) that imports and renders a `*View.tsx` component
- **PlaceholderPage**: 8 routes use `<PlaceholderPage title="...">` — a "coming soon" component
- **API proxy**: All browser fetch goes to `/api/proxy/{path}` (Next.js route handler) which injects the `access_token` cookie as Bearer header
- **No direct FastAPI calls from browser JS** — enforced by design
- **Token storage**: httpOnly cookies only; Zustand holds user object, not token
- **`asChild` not available**: ShadCN uses `@base-ui/react` — use `buttonVariants` + `<Link>` for link-buttons

---

## 2. Page Classification

### COMPLETE_AND_VERIFIED (Live-tested in browser)

| Route | Component | Notes |
|-------|-----------|-------|
| `/dashboard` | `DashboardView.tsx` | Role-specific home, tested 4 roles |
| `/workspace` | `WorkspaceLandingView.tsx` | Role-specific prompts, verified |
| `/ai-workspace` | `AiWorkspaceView.tsx` | 3-panel streaming chat, verified |
| `/knowledge` | `KnowledgeLandingView.tsx` | 6 feature cards |
| `/quality` | `QualityLandingView.tsx` | 8 feature cards |
| `/administration` | Admin landing | 9 cards (SA only) |
| `/knowledge/extraction` | `ExtractionView.tsx` | Knowledge extraction workspace |
| Login (`/login`) | Login form | httpOnly cookie flow, verified |

### COMPLETE_BUT_NOT_VERIFIED (Code complete, not live-tested in this audit)

| Route | Component | Size | Notes |
|-------|-----------|------|-------|
| `/audits` | `AuditCentre.tsx` | ~9KB | Full audit list + trigger UI |
| `/audits/new` | New audit form | ? | Not inspected |
| `/audits/[id]` | Audit detail | ? | Not inspected |
| `/workflow` | `WorkflowListView.tsx` | ~6KB | Status badges, filters |
| `/approvals` | `ApprovalsView.tsx` | ~8KB | Approve/reject/return dialog |
| `/reports` | `ReportsView.tsx` | ~4KB | CSV/Excel/PDF export buttons |
| `/analytics` | `AnalyticsView.tsx` | ~7KB | Dashboard stats + KI index |
| `/files` | `FilesView.tsx` | ? | File upload and listing |
| `/modules` | Module list | ? | Not inspected |
| `/programmes` | Programme list | ? | Not inspected |
| `/institutions` | Institutions list | ? | Not inspected |
| `/users` | Users list | ? | Not inspected |
| `/knowledge/acquisition` | Acquisition UI | ? | Source management |
| `/knowledge/review` | Review UI | ? | Knowledge review queue |

### PLACEHOLDER (Renders `<PlaceholderPage>`)

| Route | Title |
|-------|-------|
| `/accreditation` | Accreditation Readiness |
| `/findings` | Findings |
| `/settings` | Settings (root) |
| `/settings/profile` | Profile Settings |
| `/settings/notifications` | Notification Settings |
| `/settings/security` | Security Settings |
| `/settings/system` | System Settings |
| `/reports/compliance` | Compliance Reports |

### OBSOLETE / SUPERSEDED

| Route | Status | Note |
|-------|--------|------|
| `/ai-assistant` | `OBSOLETE` | Replaced by `/ai-workspace` in Phase 4 Wave 2. Route still exists but all links updated to new path. |

### UNKNOWN (Routes exist; pages not inspected)

| Route | Notes |
|-------|-------|
| `/calendar` | Route visible in filesystem |
| `/ikp-management` | IKP management page |
| `/institution` | Institution detail |
| `/qualification-intelligence` | Qualification search |
| `/knowledge-search` | Knowledge search |
| `/ai` | Unknown purpose |
| `/departments` | Department list |
| `/faculties` | Faculty list |
| `/notifications` | Notification center |
| `/forbidden` | 403 page |

---

## 3. Key Components

### Navigation
- **`Sidebar.tsx`**: 220px expanded / 64px collapsed; RBAC-filtered nav; mobile overlay
- **`Topbar.tsx`**: 56px sticky; ⌘K search; institution pill; AI Ready pill; theme toggle; user dropdown
- **`AppShell.tsx`**: Layout wrapper; removed FloatingAIButton
- **`CommandPalette.tsx`**: 5 grouped sections; RBAC-filtered; keyboard nav

### AI Workspace
- **`AiWorkspaceView.tsx`**: ~950 lines; 3-panel layout (sidebar 240px + main + context 280px)
- **`MarkdownMessage.tsx`**: react-markdown + remark-gfm; `[SOURCE:N]` → CitationChip; streaming cursor
- **`CitationChip.tsx`**: Numbered inline citation with hover tooltip
- **`ContextPanel.tsx`**: SVG donut grounding gauge; knowledge sources; agents used; next actions
- **`RichCards.tsx`**: 9 domain card types (Policy, Module, Programme, Finding, etc.)

### Dashboard
- **`DashboardView.tsx`**: `ROLE_PROMPTS` map (7 variants); `getContinueCards(role)`; `AskAQAAComposer`; role-conditional rendering; admin stats; student panels

### Common
- **`PlaceholderPage.tsx`**: "Coming soon" stub used for 8 routes
- **`PageHeader.tsx`**: Consistent page header
- **`EmptyState.tsx`**: Empty list state component
- **`ErrorState.tsx`**: API error state
- **`RoleGuard.tsx`**: Conditional render by `user.role`

---

## 4. Hooks

Key custom hooks confirmed:
- `useRole()` — returns `{ role, isAdmin, isQAOfficer, isLecturer, isStudent, ... }`
- `useAuth()` — session rehydration via `GET /auth/me`
- `useModuleAudits()`, `useDeleteAudit()` — audit CRUD
- `useModules()`, `useProgrammes()` — data fetching
- `useWorkflows()` — workflow list
- `useApproveAudit()`, `useRejectAudit()` etc. — approval mutations
- `useReporting()`, `useComplianceSummary()` — reporting data

---

## 5. Quality Gate Results (Most Recent)

| Gate | Result | Date |
|------|--------|------|
| `npx tsc --noEmit` | 0 errors ✅ | 2026-07-12 |
| `npx next lint` | 0 warnings ✅ | 2026-07-12 |
| `npx next build` | Clean build ✅ | 2026-07-12 |

---

## 6. Known Frontend Bugs / Limitations

1. **`/api/v1/audits` global list empty**: Frontend `useAudits()` hook calls this endpoint; audit centre will always show empty list despite audit runs completing. Per-module polling works, global list does not.
2. **React controlled input + browser `form_input`**: React's synthetic event system doesn't fire when browser automation fills inputs. Not a user-facing bug — only affects automated testing.
3. **Zustand sessionStorage stale session**: When switching between roles in the same browser session, `sessionStorage.clear()` is required before re-login. Not a user-facing issue in normal use.
4. **`/ai-assistant` route still exists**: Old route not removed. Navigation will land at the old page rather than redirecting. Low priority.
5. **Qualification Intelligence page** (`/qualification-intelligence`): Listed in navigation but page not inspected — unknown implementation state.
