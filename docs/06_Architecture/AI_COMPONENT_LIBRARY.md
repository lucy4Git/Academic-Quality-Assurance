# AI Component Library

**AQAA v4.0 · Phase 4 Wave 2**

All components live in `frontend/src/components/ai/`.

---

## MarkdownMessage

`src/components/ai/MarkdownMessage.tsx`

Renders AI response text as rich markdown with citation chip injection and a streaming cursor.

### Props

```typescript
interface MarkdownMessageProps {
  content: string;          // Raw response text (may contain [SOURCE:N] markers)
  citations?: Citation[];   // Citation objects indexed from 0
  isStreaming?: boolean;    // Shows animated cursor while true
  className?: string;
}
```

### Features

- **react-markdown + remark-gfm** — GFM tables, task lists, strikethrough
- **[SOURCE:N] injection** — Replaces markers with `CitationChip` components in paragraph text
- **Code blocks** — Dark code block with language label and copy button
- **Tables** — Wrapped in `overflow-x-auto` container
- **Links** — Open in new tab
- **Streaming cursor** — Animated blue pulse dot when `isStreaming: true`

### Usage

```tsx
<MarkdownMessage
  content={message.content}
  citations={message.citations ?? []}
  isStreaming={message.isStreaming}
/>
```

---

## CitationChip

`src/components/ai/CitationChip.tsx`

Inline citation reference rendered as a numbered circle with hover tooltip.

### Props

```typescript
// CitationChip
interface CitationChipProps {
  index: number;          // 0-based; renders as index+1
  citation?: Citation;    // If undefined, chip renders without tooltip
}

// Citation type (from ai-assistant.ts)
interface Citation {
  source_id: string;
  title: string;
  entity_type: string;
  snippet?: string;
  relevance_score?: number;
  source_document?: string;
}
```

### Tooltip contents

- Entity type colour dot
- Source title
- Entity type badge
- Snippet (italic, 3-line clamp)
- Relevance bar + percentage
- "Source" button (copies `source_document` to clipboard)

### Helper

```typescript
// Parse [SOURCE:N] text and return ReactNode[] with chips
injectCitationChips(text: string, citations: Citation[]): React.ReactNode[]
```

---

## ContextPanel

`src/components/ai/ContextPanel.tsx`

Right-side "Oracle" panel showing live context for the current AI response.

### Props

```typescript
interface ContextPanelProps {
  institutionCode: string;
  groundingScore?: number;        // 0–1 float
  groundingStatus?: "grounded" | "partially_grounded" | "no_source_found";
  sources: StreamSource[];
  citations: Citation[];
  agents: string[];
  nextActions: string[];
  onActionClick: (action: string, route?: string) => void;
  onClose: () => void;
  messageCount: number;
}
```

### Sub-components

**GroundingGauge** — SVG donut chart
- 56px circle, `stroke-dashoffset` for arc
- Color-coded: green ≥ 80%, amber ≥ 50%, red < 50%
- Shows `pct%` and status label beside the gauge

**SourceItem** — Single knowledge source row
- Entity type colour dot
- Title + entity type + confidence %

**CitationItem** — Single citation row  
- Numbered blue circle
- Title + snippet + relevance %

### ACTION_ROUTES mapping

Next-action strings from the AI are matched to frontend routes:

```typescript
const ACTION_ROUTES: Record<string, string> = {
  "Create audit": "/audits",
  "Generate report": "/reports",
  "Upload missing evidence": "/files/upload",
  "Open module workspace": "/workspace",
  "Search related policies": "/knowledge-search",
  "Start accreditation review": "/accreditation",
  "View findings": "/findings",
  "Open knowledge search": "/knowledge-search",
};
```

---

## RichCards

`src/components/ai/RichCards.tsx`

Nine domain-specific card components for embedding structured entities in AI responses.

All share the `CardShell` base with:
- 3px left accent bar (colour-coded by domain)
- 7px icon container
- Badge text above title
- Arrow icon on hover

### Cards

| Component | Accent | Domain |
|-----------|--------|--------|
| `PolicyCard` | violet | Institutional policies |
| `ModuleCard` | blue | Academic modules |
| `ProgrammeCard` | indigo | Degree programmes |
| `FindingCard` | rose | Audit findings |
| `AccreditationCard` | amber | Accreditation bodies |
| `AuditCard` | emerald | Audit runs |
| `InstitutionCard` | slate | Institutions |
| `QualificationCard` | teal | NQF qualifications |
| `EvidenceCard` | cyan | Uploaded evidence |

### Example

```tsx
<ModuleCard
  code="CSC401"
  title="Advanced Algorithms"
  nqfLevel={7}
  credits={16}
  status="active"
/>

<FindingCard
  title="Missing moderation reports for Semester 1"
  severity="major"
  area="Assessment Compliance"
  status="open"
/>

<PolicyCard
  title="Assessment and Moderation Policy"
  version="2.3"
  status="approved"
  policyType="Academic"
/>
```

### Chip component

```tsx
// Reusable badge inside cards
<Chip label="NQF 7" color="bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300" />
```

---

## Design tokens used across components

| Token | Value | Usage |
|-------|-------|-------|
| `bg-blue-600` | Electric blue | User bubbles, primary actions, send button |
| `bg-card` | Theme card bg | Assistant response bubbles |
| `border-border` | Theme border | Cards, panel dividers |
| `text-muted-foreground` | Secondary text | Timestamps, labels, captions |
| `rounded-2xl` | 16px radius | Message bubbles |
| `rounded-xl` | 12px radius | Cards, inputs, buttons |
| `shadow-sm` | Light shadow | Cards |

All components use Tailwind CSS v3 with `dark:` variants and CSS custom properties (`--background`, `--foreground`, etc.) from the `globals.css` design token layer.
