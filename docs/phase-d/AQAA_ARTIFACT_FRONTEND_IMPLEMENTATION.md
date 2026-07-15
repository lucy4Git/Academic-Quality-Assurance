# AQAA Artifact Frontend Implementation

**Phase D5 · Artifact Engine Frontend**
**Date:** 2026-07-15

---

## Component Architecture

### `ArtifactPanel` (`frontend/src/components/ai/ArtifactPanel.tsx`)
Main panel component wired into the AI Workspace right panel as a tab.

**Layout:**
- Desktop: right-side 300px panel (tab: Context | Artifacts)
- Full-screen: toggled per artifact via Maximize button
- Keyboard: Escape closes detail view; Enter triggers actions; Tab navigates buttons

**Sub-components:**
| Component | Purpose |
|-----------|---------|
| `ArtifactPanel` | Outer panel — manages list/detail state, refresh |
| `ArtifactList` | Scrollable list of artifacts for the active conversation |
| `ArtifactDetailView` | Full detail view — content, actions, source trace |
| `ArtifactCard` | Inline card shown in the message flow |
| `ApprovalBadge` | Colored badge: pending / approved / rejected |
| `StatusIcon` | Icon: saved / archived / versioned / draft |

### AI Workspace Integration (`AiWorkspaceView.tsx`)
- Right panel now has **Context** and **Artifacts** tabs
- `activeSessionId` passed to `ArtifactPanel` as `conversationId`
- Panel refreshes on tab switch and manual refresh button

---

## Features Implemented

### Artifact List
- Loads from `GET /artifacts?conversation_id={id}`
- Shows: title, type label, status icon, version number
- Selected artifact highlighted with blue border

### Artifact Detail View
- Loads from `GET /artifacts/{id}`
- Shows: type, title (editable), version, status, approval badge
- Content: rendered Markdown if available, else JSON pretty-print
- Source trace: expandable section showing evidence, findings, framework, assessment counts

### Rename
- Click title to enter edit mode
- `Enter` or ✓ button → `PATCH /artifacts/{id}` with `{title}`
- `Escape` cancels

### Archive / Restore
- Archive: `POST /artifacts/{id}/archive` → status becomes `archived`
- Restore: `POST /artifacts/{id}/restore` → status becomes `saved`
- Panel closes after archive; refreshes list after restore

### Export
**Verified formats only:**
| Format | Endpoint | Output |
|--------|---------|--------|
| JSON | `GET /artifacts/{id}/export?format=json` | `artifact_{id}.json` download |
| Markdown | `GET /artifacts/{id}/export?format=markdown` | `artifact_{id}.md` download |

PDF and DOCX are **not** shown — they are not implemented in the backend. The spec requires "do not claim an export unless it works."

### Version History
- `parent_artifact_id` links versions
- `version_number` displayed in detail header
- Full version browsing: future work (Phase E)

### Approval State
- `ApprovalBadge` shows for pending / approved / rejected
- Approval action (`POST /artifacts/{id}/approve`) requires QA Officer role — not shown to Lecturers

---

## API Calls Used
```
GET  /artifacts?conversation_id={id}    List artifacts
GET  /artifacts/{id}                     Get detail
PATCH /artifacts/{id}                   Rename
POST /artifacts/{id}/archive             Archive
POST /artifacts/{id}/restore             Restore
GET  /artifacts/{id}/export?format=...  Export (json | markdown only)
```

---

## Accessibility
- All interactive elements have `aria-label`
- Keyboard navigable (Tab order follows visual order)
- Focus trapped to fullscreen mode
- `Escape` closes fullscreen
- Edit mode auto-focuses title input via `useEffect`

---

## Pass/Fail Summary
| Feature | Result |
|---------|--------|
| Artifact panel in workspace | ✅ |
| Context/Artifacts tab switching | ✅ |
| List artifacts by conversation | ✅ |
| Artifact detail view | ✅ |
| Rename inline | ✅ |
| Archive | ✅ |
| Restore | ✅ |
| Export JSON | ✅ |
| Export Markdown | ✅ |
| Source trace display | ✅ |
| Approval badge display | ✅ |
| Full-screen toggle | ✅ |
| Mobile/tablet (full-screen) | ✅ via fullscreen toggle |
| No PDF export shown | ✅ (not implemented) |
| No DOCX export shown | ✅ (not implemented) |
