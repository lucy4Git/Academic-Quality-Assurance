# AI Workspace UI — Implementation Guide

**Phase:** 2 — Commercial UI/UX Modernization  
**Sprint:** 3 — Claude-Style AI Workspace  
**Status:** Complete  
**Date:** 2026-07-05

---

## Overview

Sprint 3 rewrites `/ai-workspace` from a 2-panel chat widget into a full 3-panel commercial AI workspace modelled on Claude, ChatGPT Team, and NotebookLM. All backend API hooks and tenant-isolation logic from RC4 are preserved intact; only the visual and interaction layer is replaced.

---

## File Structure

```
frontend/src/app/(main)/ai-workspace/
└── AiWorkspaceView.tsx    ← Full workspace (single file, all panels inlined)
```

All components are co-located in `AiWorkspaceView.tsx` to keep the session state and panel coordination in one place. Sub-components are exported as module-private functions.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  [LEFT SIDEBAR w-64]  [CENTRE PANEL flex-1]  [RIGHT PANEL w-72]  │
├─────────────────┬────────────────────────────┬───────────────────┤
│  New conversation│  AQAA AI Workspace topbar  │  Sources & Context│
│  Institution ctx │  ─────────────────────    │  ─────────────────│
│  Session history │  Message thread            │  Source cards     │
│  ─────────────   │    User bubble (indigo)    │  Agent cards      │
│  Quick links     │    AQAA card (white/card)  │  Suggested actions│
│                  │    Thinking animation      │                   │
│                  │  ─────────────────────    │                   │
│                  │  Prompt composer           │                   │
└─────────────────┴────────────────────────────┴───────────────────┘
```

The right panel slides in/out with Framer Motion `AnimatePresence` and is toggled via the Sources button in the centre topbar.

---

## Component Reference

### `ThinkingAnimation`

Shown in the centre panel while any mutation is pending (`ask.isPending || agentRouter.isPending || multiAgent.isPending`).

- 5 sequential steps, each appearing with `opacity` + `x` Framer Motion transition
- Step advances every 1600 ms via `setInterval` (reset on mount, cleared on unmount)
- Active step: `text-indigo-600 font-medium` + `Loader2` spinning icon
- Completed steps: `text-muted-foreground` + `CheckCircle2` icon
- Pending steps: faint opacity + empty circle

### `MessageBubble`

Renders both user and assistant messages. Role-discriminated at the top level.

**User:** Right-aligned, `bg-indigo-600` rounded bubble, timestamp below.

**Assistant:** Left-aligned card with:
- Agent badges (mapped from `msg.agents[]` → icon + colour via `AGENT_ICONS` / `AGENT_COLOURS` records)
- AQAA brain header + provider/model badge (right-aligned in header row)
- Response text (`whitespace-pre-wrap`)
- Confidence bar (28-wide, colour: green ≥70%, amber ≥45%, red <45%)
- Inline source chips (up to 4, overflow count links to right panel)
- Action row: Copy (clipboard API + toast), Export (blob download `.txt`), timestamp
- Multi-agent contribution cards (2-column grid, shows agent name + confidence %)
- Follow-up question pills (up to 3, click to re-submit)

### `SourceCard`

Rendered in the right panel for each `SourceChunk | string` source.

- Title from `source.title || source.entity_key`
- Entity type badge + relevance score (colour-coded same thresholds as confidence)
- Text snippet (`source.text`) — 3-line clamp
- Two action buttons: **Search** (navigates to `/knowledge-search?q=<title>`) and **Cite** (copies `entity_key` to clipboard + toast)

### `RightPanel`

Reads the **last assistant message** from the message list and displays its sources, agents, and next actions. When no sources exist, shows an empty state illustration.

Suggested actions are drawn from `msg.nextActions`. Falls back to a static set of 4 actions (Create audit, Generate report, Upload missing evidence, Search related policies) when the message has none. Actions are routed via `ACTION_ROUTES` record → `router.push()`.

### `LeftSidebar`

- **New conversation** button calls `createSession.mutateAsync()` → sets `activeSessionId` and clears `messages`.
- **Institution selector** (admin only): `<select>` over `ACTIVE_INSTITUTIONS` constant.
- **Institution badge** (non-admin): static display of `user.institution_code`.
- **Session list**: reads `useChatSessions()`, renders clickable session rows with title, message count, and delete icon. Clicking a session sets `activeSessionId` and clears the local message list (messages reload implicitly on next send because `session_id` is passed to the API).
- **Quick links**: static `<a>` tags to `/knowledge-search`, `/files`, `/audits`, `/reports`.

### `EmptyState`

Shown when `messages.length === 0 && !isLoading`.

- Animated brain icon (scale-in entrance)
- 6 suggestion cards sourced from `useSuggestedPrompts(institutionCode)` when data is available; falls back to `EMPTY_PROMPTS` constant.
- Each card: category chip + label; click calls `handleSubmit(prompt)` directly.
- Cards stagger-animate in with Framer Motion.

### `PromptComposer`

- Auto-resizing `<textarea>` (rows=1, max-height 160px via inline style)
- Slash command menu: detects when the last word starts with `/`, filters `SLASH_COMMANDS`, renders a pop-up above the input. Selecting a command replaces the slash word with the command label + `: `.
- **Multi-agent toggle**: pill button — purple when active, muted when off.
- **Send button**: calls `handleSubmit(value)`, shows `Loader2` spinner while loading.
- **Session meta row**: shown when `messageCount > 0` — displays message count, institution, and Clear chat link.
- **Keyboard**: Enter sends, Shift+Enter newlines, Escape closes slash menu.

---

## Data Flow

### Single-agent path (default)

```
handleSubmit(q)
  → agentRouter.mutateAsync(q)        // POST /ai-assistant/route
      routerResult.agent_mode         // intent detection
  → ask.mutateAsync({ question, mode, institution_code, session_id })
      // POST /ai-assistant/ask
  → append assistant WorkspaceMessage
```

### Multi-agent path (`useMultiAgentMode = true`)

```
handleSubmit(q)
  → multiAgent.mutateAsync({ prompt, institution_code, session_id })
      // POST /ai-assistant/multi-agent
  → append assistant WorkspaceMessage (contributions mapped to inline cards)
```

Both paths are gated behind `isAdmin && !institutionCode` — the send button is disabled and shows a warning badge in the topbar.

---

## State

| State var | Type | Purpose |
|-----------|------|---------|
| `institutionCode` | `string` | Tenant scope; initialised from `user.institution_code` for non-admins |
| `activeSessionId` | `string \| null` | Passed as `session_id` to all AI calls |
| `messages` | `WorkspaceMessage[]` | Local message list (not fetched from API — session history is separate) |
| `input` | `string` | Controlled textarea value |
| `useMultiAgentMode` | `boolean` | Switches between single and multi-agent path |
| `showRightPanel` | `boolean` | Framer Motion toggle for right panel visibility |

---

## WorkspaceMessage Interface

```ts
interface WorkspaceMessage {
  id: string;                          // crypto.randomUUID()
  role: "user" | "assistant";
  content: string;
  agents?: string[];                   // agent names shown as badges
  isMultiAgent?: boolean;
  confidence?: number;                 // 0–1, drives confidence bar colour
  sources?: (SourceChunk | string)[];  // SourceChunk from single-agent; string[] from multi-agent contributions
  nextActions?: string[];
  followUps?: string[];
  provider?: string;
  model?: string;
  timestamp: Date;
  routerResult?: AgentRouterResponse;
  contributions?: { agent: string; confidence: number; summary?: string }[];
}
```

---

## Constants

| Constant | Purpose |
|----------|---------|
| `ACTIVE_INSTITUTIONS` | Pilot institutions shown in admin selector |
| `AGENT_ICONS` | Maps agent mode string → Lucide icon component |
| `AGENT_COLOURS` | Maps agent mode string → Tailwind class string (badge colours) |
| `SLASH_COMMANDS` | `/audit`, `/policy`, `/evidence`, `/report`, `/qualification` |
| `ACTION_ROUTES` | Maps natural-language action label → Next.js route |
| `THINKING_STEPS` | 5-step animation sequence |
| `EMPTY_PROMPTS` | 6 fallback suggestion cards |

---

## `?q=` Pre-fill Protocol

`MiniAIWidget` and `AISuggestions` on the dashboard navigate to `/ai-workspace?q=<encoded-question>`. On mount, `AiWorkspaceView` reads `window.location.search`, extracts `q`, sets it as the initial `input` value, and clears the param from the URL with `window.history.replaceState`. The user can then edit or send immediately.

---

## Accessibility

- All interactive elements have `aria-label`
- Session list items use `role="button"` + `tabIndex={0}` + `onKeyDown` Enter handler
- Textarea has `aria-label="Message input"`
- Institution selector has `aria-label="Select institution"`
- Right panel close button has `aria-label="Close right panel"`
- Slash menu closes on Escape
- All colour-coded information (confidence, relevance score) has an accompanying text label

---

## Performance Notes

- `MessageBubble` is wrapped in `React.memo` — avoids re-rendering the entire message list on every keystroke in the composer
- `ThinkingAnimation` is only mounted during `isLoading`; its interval is cleaned up on unmount
- Framer Motion `AnimatePresence` is used for the right panel so the DOM node is removed when hidden (not just `display:none`)
- No Recharts or other chart library is used in this component — no lazy-loading required

---

## Phase 3 Integration Points

| Current mock | Future API |
|-------------|-----------|
| `EMPTY_PROMPTS` fallback | `GET /api/v1/ai-assistant/suggested-prompts?institution_code=` (already wired — fallback only triggers when empty) |
| Static action route map | `routerResult.suggested_next_actions` from agent router (already used when available) |
| Session list titles | Session rename API (planned) |
