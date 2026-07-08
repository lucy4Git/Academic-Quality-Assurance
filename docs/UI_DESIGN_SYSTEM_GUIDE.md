# UI Design System Guide — Quantum Precision

## Design Language

**Quantum Precision** — AI-native enterprise aesthetic. Deep, calm, intentional. Inspired by Linear, Vercel, and ChatGPT Enterprise. Every element earns its place.

---

## Colour Tokens (`globals.css`)

### Semantic tokens (use these in components)
```css
--background        /* page background */
--foreground        /* primary text */
--card              /* card surface */
--card-foreground   /* card text */
--muted             /* subtle fill */
--muted-foreground  /* secondary text */
--border            /* subtle borders */
--primary           /* electric blue — CTAs, active states */
--primary-foreground/* text on primary */
--sidebar-background/* deep charcoal — sidebar only */
--sidebar-foreground/* sidebar text */
--sidebar-border    /* sidebar dividers */
--sidebar-accent    /* sidebar hover/skeleton */
```

### Values
| Token | Light | Dark |
|-------|-------|------|
| `--background` | `220 14% 96%` | `224 71% 4%` |
| `--card` | `0 0% 100%` | `224 50% 7%` |
| `--sidebar-background` | `224 71% 7%` | `224 71% 3%` |
| `--primary` | `221 83% 53%` | `221 83% 63%` |
| `--radius` | `0.75rem` | `0.75rem` |

---

## Component Classes

### `.aqaa-card`
Standard content card. White background, `rounded-xl`, `border border-border/60`, `shadow-sm`, `transition-shadow`. Use for all workspace landing cards and dashboard tiles.

```html
<div class="aqaa-card p-6">...</div>
```

### `.workspace-card`
Larger card variant for workspace landing pages. Adds `p-6 hover:shadow-md`.

### `.nav-item`
Sidebar navigation link. Dark surface, icon + label, active state with left border indicator (`::before` pseudo-element), hover fill. Collapses to icon-only in collapsed sidebar.

### `.topbar-search`
Premium search button in topbar. `flex items-center gap-2`, `rounded-lg border border-border/40`, `bg-muted/60`, `text-sm text-muted-foreground`, `min-w-[180px]`. Right-side `⌘K` kbd element.

### `.status-pill`
Inline badge for status indicators. `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium`. Use with a coloured dot (`●`) for AI status, institution badges.

---

## Typography

| Use | Class |
|-----|-------|
| Page title | `text-2xl font-bold tracking-tight text-foreground` |
| Section heading | `text-sm font-semibold text-foreground` |
| Card label | `font-semibold text-foreground` |
| Card description | `text-[12.5px] text-muted-foreground leading-relaxed` |
| Greeting subtitle | `text-xs font-semibold uppercase tracking-wider text-muted-foreground` |
| Badge text | `text-[10px] font-semibold uppercase tracking-wide` |
| Meta text | `text-[11px] text-muted-foreground/60` |

---

## Spacing

- Page padding: `px-6 py-8` (AppShell main content)
- Max content width: `max-w-[1100px]` for workspace landings, `max-w-[1440px]` for shell
- Card padding: `p-6` standard, `p-4` compact
- Section gap: `space-y-8` between major sections, `space-y-4` between sub-sections

---

## Icons

All icons from `lucide-react`. Standard sizes:
- Nav icon (collapsed): `h-5 w-5`
- Nav icon (expanded): `h-4 w-4`
- Card icon container: `w-9 h-9 rounded-xl`
- Card icon: `h-4 w-4`
- Topbar icon: `h-4 w-4`
- Micro icon: `h-3 w-3` or `h-3.5 w-3.5`

---

## Dark Mode

Theme managed by `next-themes` (`ThemeProvider`). CSS uses `@media (prefers-color-scheme: dark)` and `.dark` class on `<html>`. Always verify both modes when editing design tokens or component styles.

---

## Adding New Workspace Cards

1. Add the card definition to the `CARDS` array in the workspace page
2. Set `roles` to the minimum role array (import from local constants or `@/lib/rbac`)
3. Choose a `iconColor` from the existing palette (blue, violet, emerald, amber, rose, indigo, teal, slate, gray)
4. Use an existing `href` (prefer existing routes over creating new ones)

No changes to sidebar, topbar, RBAC config, or backend are needed for new landing cards.
