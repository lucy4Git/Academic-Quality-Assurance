# AI Workspace Architecture

**Phase 4 Wave 2 — AQAA v4.0**

---

## Overview

The AI Workspace is a three-panel conversational intelligence interface that serves as AQAA's primary user surface. It replaces the traditional CRUD-first workflow with an AI-first conversation model designed for Higher Education Quality Assurance professionals.

---

## Layout Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  App Shell (AppShell.tsx)                                        │
│  ┌──────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │ LEFT     │  │ MAIN CHAT            │  │ RIGHT CONTEXT    │  │
│  │ SIDEBAR  │  │                      │  │ PANEL            │  │
│  │          │  │  Empty State         │  │                  │  │
│  │ 240px    │  │  or                  │  │ 280px            │  │
│  │ fixed    │  │  Conversation        │  │ animated slide   │  │
│  │          │  │  Messages            │  │                  │  │
│  │ overflow │  │                      │  │ overflow-y-auto  │  │
│  │ -y-auto  │  │  Composer            │  │                  │  │
│  └──────────┘  └──────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Tree

```
AiWorkspaceView
├── ConversationSidebar           (left — 240px)
│   ├── New conversation button
│   ├── Search input
│   ├── Institution selector      (admin only)
│   ├── Pinned sessions list
│   └── Recent sessions list
│
├── Main Chat Column              (flex-1)
│   ├── Topbar
│   │   ├── Brain icon + title
│   │   ├── Institution badge
│   │   └── Context panel toggle
│   ├── Message area
│   │   ├── EmptyState            (when messages.length === 0)
│   │   │   ├── Sparkles hero icon
│   │   │   ├── Welcome headline
│   │   │   └── Suggested task grid (3-col, backend-seeded)
│   │   └── MessageBubble[]
│   │       ├── User bubble        (right-aligned, blue)
│   │       └── Assistant bubble   (left-aligned, card)
│   │           ├── Agent badge
│   │           ├── Grounded badge
│   │           ├── MarkdownMessage
│   │           ├── Action toolbar (copy, export .md, regenerate)
│   │           └── Follow-up suggestions
│   └── PromptComposer
│       ├── Slash command dropdown
│       ├── Auto-expanding textarea
│       ├── Attachment placeholder
│       ├── Voice placeholder
│       └── Send / Stop button
│
└── ContextPanel (right — 280px, AnimatePresence)
    ├── Institution header
    ├── Grounding Score (SVG donut gauge)
    ├── Citations list
    ├── Knowledge Sources list
    ├── Agents used (with status checkmark)
    └── Next Actions (route-linked buttons)
```

---

## Data Flow

### Streaming Path (primary)

```
User submits question
  → handleSubmit()
  → POST /api/proxy/ai-assistant/ask (SSE stream)
  → askStream() async generator
  → Events parsed: start | chunk | token | sources | metadata | done | error
  → React state updated per event:
      start    → agents[]
      chunk    → content accumulation
      sources  → sources[], groundingScore, nextActions, followUps
      metadata → citations[], groundingStatus
      done     → isStreaming: false, provider, model
  → MarkdownMessage re-renders on every chunk
  → ContextPanel updates on sources/metadata events
```

### Session Management

```
createSession()  → POST /ai-assistant/sessions
useChatSessions() → GET /ai-assistant/sessions (polling 30s)
deleteSession()  → DELETE /ai-assistant/sessions/{id}
pinnedIds       → localStorage "aqaa:pinned-sessions" (JSON array)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/app/(main)/ai-workspace/AiWorkspaceView.tsx` | Main view — all workspace state |
| `src/components/ai/MarkdownMessage.tsx` | Markdown + citation chip renderer |
| `src/components/ai/ContextPanel.tsx` | Right panel — grounding, sources, agents |
| `src/components/ai/CitationChip.tsx` | Inline citation [SOURCE:N] → hover chip |
| `src/components/ai/RichCards.tsx` | 9 domain card types for AI responses |
| `src/lib/api/ai-assistant.ts` | `askStream()` SSE generator + types |
| `src/hooks/useAiAssistant.ts` | `useAsk`, `useChatSessions`, etc. |

---

## SSE Event Schema

```typescript
type StreamEvent =
  | { type: "start";    agents: string[] }
  | { type: "chunk";    content: string }
  | { type: "token";    content: string }
  | { type: "sources";  sources: StreamSource[]; confidence_score: number;
                        suggested_next_actions: string[];
                        follow_up_questions?: string[] }
  | { type: "metadata"; citations: Citation[]; unsupported_claims: string[];
                        grounding_status: "grounded"|"partially_grounded"|"no_source_found" }
  | { type: "done";     provider: string; model: string }
  | { type: "error";    message: string }
```

---

## Slash Commands

| Command | Action |
|---------|--------|
| `/new` | Clears conversation, starts fresh |
| `/audit` | Labels query as audit analysis |
| `/policy` | Labels query as policy search |
| `/module` | Labels query as module query |
| `/programme` | Labels query as programme review |
| `/evidence` | Labels query as evidence check |
| `/finding` | Labels query as finding search |
| `/help` | Inserts command reference into composer |
| `/report` | Labels query as report generation |
| `/qualification` | Labels query as NQF/credit analysis |

---

## State Management

| State | Location | Persistence |
|-------|----------|-------------|
| `messages` | React useState | In-memory only |
| `activeSessionId` | React useState | In-memory only |
| `institutionCode` | React useState | In-memory |
| `pinnedIds` | React useState | localStorage |
| `user` / `isAuthenticated` | Zustand (auth.store) | sessionStorage |
| Session list | TanStack Query cache | Memory (30s TTL) |

---

## Grounding Score

The `GroundingGauge` SVG component in `ContextPanel.tsx`:
- Draws a 56px donut via `stroke-dashoffset` animation
- Score from `StreamMetadataEvent.confidence_score` (0–1 float → 0–100%)
- Green ≥ 80%, Amber ≥ 50%, Red < 50%
- `groundingStatus` adds a warning banner when `"no_source_found"`

---

## Export

`exportMarkdown()` in `MessageBubble`:
- Compiles response + citation list into `.md` format
- Creates blob URL and triggers browser download
- Filename: `aqaa-response-YYYY-MM-DD.md`
