# AQAA Regulatory Engine — Frontend Integration

**Phase C | Version 1.0 | 2026-07-14**

---

## Architecture

The frontend uses the standard AQAA proxy pattern:
- Browser → Next.js API proxy (`/api/proxy/{path}`) → FastAPI (`http://localhost:8000/api/v1/{path}`)
- JWTs live in `httpOnly` cookies only — JavaScript never accesses tokens directly
- All regulatory API calls go through `frontend/src/lib/api/regulatoryFramework.ts`

---

## Key Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/framework-management` | `FrameworkManagement.tsx` | Browse authorities + frameworks with TEST FIXTURE badges |
| `/regulatory-readiness` | `RegulatoryReadiness.tsx` | Assessment results, compliance scores, mandatory failure tracking |
| `/quality` | `quality/page.tsx` | Workspace hub with links to all regulatory workspaces |

---

## TypeScript Types

```typescript
// frontend/src/lib/api/regulatoryFramework.ts

interface RegulatoryAuthority {
  id: string;
  code: string;
  name: string;
  is_test_fixture: boolean;  // computed from name containing [TEST FIXTURE]
  // ...
}

interface QualityFramework {
  id: string;
  code: string;
  versions: FrameworkVersionBrief[];
  is_test_fixture: boolean;  // computed field
  // ...
}
```

---

## TEST FIXTURE Badge

Displayed on authority and framework cards when `is_test_fixture = true`:

```tsx
{framework.is_test_fixture && (
  <span className="text-[10px] px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded font-medium">
    TEST FIXTURE
  </span>
)}
```

This disclosure is mandatory — users must know when they are viewing non-authoritative regulatory stubs.

---

## Null Safety

The `versions` array on `QualityFramework` must always be null-safe:

```tsx
// Correct
const activeVersions = (framework.versions ?? []).filter((v) => v.status === "active");

// Wrong — will throw if versions is undefined
const activeVersions = framework.versions.filter((v) => v.status === "active");
```

The backend `list_frameworks()` eagerly loads versions via `selectinload`, so `versions` should never be null after the C9 fix. The `?? []` guard provides safety against future regressions.

---

## ShadCN UI Notes

The installed ShadCN UI uses `@base-ui/react`, not Radix UI. The `asChild` prop does **not** exist. Use `buttonVariants` + `<Link>` directly for link-buttons.

---

## TanStack Query Keys

| Key | Purpose |
|-----|---------|
| `["frameworks"]` | Framework list query |
| `["regulatory-authorities"]` | Authority list query |
| `["regulatory-assessments", institution_id]` | Assessment list |

Invalidate these keys after creating or updating framework data.
