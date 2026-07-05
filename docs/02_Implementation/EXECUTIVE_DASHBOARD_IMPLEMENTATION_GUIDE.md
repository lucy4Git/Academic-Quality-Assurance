# Executive Dashboard — Implementation Guide

**Phase:** 2 — Commercial UI/UX Modernization  
**Sprint:** 2 — AI-First Executive Dashboard  
**Status:** Complete  
**Date:** 2026-07-05

---

## Overview

The AQAA executive dashboard transforms the traditional admin panel into an AI-first experience modelled on Claude, ChatGPT Team, Microsoft Copilot, and Notion AI. It delivers real-time institutional intelligence, AI-generated priorities, animated health metrics, and an embedded AI assistant widget.

---

## File Structure

```
frontend/src/app/(main)/dashboard/
├── DashboardView.tsx                  ← Orchestrator (role-aware section routing)
└── components/
    ├── ExecutiveHero.tsx              ← S1: Greeting, health ring, action buttons
    ├── TodaysPriorities.tsx           ← S2: Priority task cards (from workflow API)
    ├── AIInsights.tsx                 ← S3: Animated counter metrics
    ├── RecentAIActivity.tsx           ← S4: Event timeline
    ├── InstitutionHealth.tsx          ← S5: Radial gauge + metric bars (Recharts)
    ├── FacultyOverview.tsx            ← S6: Faculty cards with sparklines (Recharts)
    ├── KnowledgeBaseHealth.tsx        ← S7: Service status with pulse indicators
    ├── AISuggestions.tsx              ← S8: Claude-style suggestion chips
    └── MiniAIWidget.tsx               ← S9: Embedded AI assistant preview
```

---

## Section Details

### S1 — ExecutiveHero
- Animated SVG circular health ring (CSS stroke-dasharray transition)
- Time-of-day greeting + institution context badge (TUT=blue, UP=red, admin=indigo)
- AI-generated one-sentence summary from dashboard metrics
- Action buttons: Ask AQAA, Start Audit (coordinator+), Upload Folder (lecturer+), Generate Report (coordinator+)
- Framer Motion entrance animation + decorative gradient blobs

### S2 — TodaysPriorities
- Reads workflow items via `useWorkflows()` hook
- Maps `returned_for_corrections` → HIGH, `pending_qa_review` → MEDIUM, others → LOW
- Falls back to realistic static tasks when no workflow data exists
- Framer Motion staggered entrance + hover slide

### S3 — AIInsights
- 6 animated counter cards: Documents Analysed, Audits Completed, Evidence Indexed, Reports Generated, Risks Detected, Recommendations
- Custom `useCounter()` hook with ease-out-cubic animation (no library dependency)
- Values derived from `useDashboardSummary()` with deterministic scaling
- Animated progress bars via Framer Motion

### S4 — RecentAIActivity
- Vertical timeline with time, icon node, event label, detail text
- 8 realistic AI events with colour-coded icons per event type
- Framer Motion staggered entrance
- Static mock data (AI audit activity log API planned for Phase 3)

### S5 — InstitutionHealth
- Recharts `RadialBarChart` with 5 health dimensions
- Animated metric bars via Framer Motion
- Lazy-loaded Recharts components via `React.lazy()` + `Suspense`
- Static scores — real API integration planned for Phase 3

### S6 — FacultyOverview
- Reads real faculties via `useFaculties()` scoped to user's institution
- Enriches with deterministic mock health/risk data per faculty index
- Recharts `AreaChart` mini sparklines (lazy-loaded, `isAnimationActive={false}`)
- Framer Motion card hover lift

### S7 — KnowledgeBaseHealth
- 6 services: Qdrant, Redis, Postgres, OpenAI, Ollama, MinIO
- Pulse-dot animated indicators via Tailwind `animate-ping`
- Static status (healthy/warning) — real health check endpoint planned for Phase 3
- MinIO shows `warning` to indicate it is architected but not yet fully wired

### S8 — AISuggestions
- 6 Claude-style rounded pill buttons
- Role-filtered: dean-only suggestions hidden from coordinators/lecturers
- Framer Motion scale-in stagger + hover scale

### S9 — MiniAIWidget
- Controlled text input → navigates to `/ai-assistant?q=...` on submit
- 4 suggested prompts (click → open AI assistant with pre-filled query)
- "Open Full AI Workspace" CTA button
- Gradient background matching indigo brand accent

---

## Role-Based Section Visibility

| Section            | Min Role             |
|--------------------|----------------------|
| ExecutiveHero      | All (student+)       |
| AISuggestions      | Lecturer             |
| MiniAIWidget       | Lecturer             |
| AIInsights         | Lecturer             |
| TodaysPriorities   | Programme Coordinator|
| RecentAIActivity   | Lecturer             |
| InstitutionHealth  | QA Officer           |
| KnowledgeBaseHealth| QA Officer           |
| FacultyOverview    | Faculty Dean         |

---

## Libraries Used

| Library          | Version | Use                         |
|------------------|---------|-----------------------------|
| framer-motion    | ^12.x   | Card animations, counters   |
| recharts         | ^3.8.1  | Radial chart, sparklines    |
| lucide-react     | ^1.21   | All icons                   |
| Tailwind CSS     | ^3.4    | Styling + animate-ping      |

---

## Performance

- Recharts components are **lazy-loaded** via `React.lazy()` + `Suspense` to prevent SSR issues and reduce initial bundle
- `FacultyOverview` cards use `React.memo` on the sparkline component
- Dashboard summary has 60s `staleTime` — no unnecessary refetches
- `DashboardViewInner` is wrapped in `React.memo` to prevent parent re-renders
- Counter animations use `requestAnimationFrame` (no `setInterval`)

---

## Phase 3 Integration Points

When the following backend endpoints are available, swap the mock data:

- `GET /api/v1/dashboard/health` → Institution health scores (S5)
- `GET /api/v1/dashboard/activity` → Recent AI activity log (S4)
- `GET /api/v1/services/health` → Service status (S7)
- `GET /api/v1/dashboard/insights` → Daily AI metrics (S3)
