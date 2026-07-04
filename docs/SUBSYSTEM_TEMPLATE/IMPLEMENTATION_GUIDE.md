# [Subsystem Name] — Implementation Guide

**Subsystem:** [Name]  
**Document Type:** Implementation Guide  
**Version:** 1.0.0  
**Status:** Draft | Active  
**Last Updated:** YYYY-MM-DD

---

## Prerequisites

Before working on this subsystem, ensure:

- [ ] You have read `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md`
- [ ] You have read `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md`
- [ ] You have read `docs/[section]/ARCHITECTURE.md` for this subsystem
- [ ] The development environment is running (`docker compose up -d`)
- [ ] All tests pass: `python -m pytest -q`

---

## Backend Implementation

### Models (`backend/app/models/`)

| Model | File | Purpose |
|-------|------|---------|
| [ModelName] | `model_name.py` | [description] |

**Key constraints:**
- [Any non-obvious constraint, e.g., tablename override]

### Schemas (`backend/app/schemas/`)

| Schema | Purpose | Used In |
|--------|---------|---------|
| [SchemaName] | Request/Response | [endpoint] |

### Services (`backend/app/services/`)

| Function | File | Description |
|----------|------|-------------|
| `function_name()` | `service.py` | [what it does] |

**Service layer rules:**
- Always filter by `institution_id` for multi-tenant queries
- Raise domain exceptions (`NotFoundError`, `DomainPermissionError`) — never HTTP exceptions
- Let `main.py` exception handlers map to HTTP status codes

### Routes (`backend/app/routes/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/[path]` | AnyAuthenticated | [description] |
| POST | `/api/v1/[path]` | CoordinatorRequired | [description] |

**Route registration in `backend/app/main.py`:**
```python
from app.routes.[module] import router as [name]_router
app.include_router([name]_router, prefix=prefix)
```

---

## Frontend Implementation

### Types (`frontend/src/types/`)

```typescript
// [typename].ts
export interface [TypeName] {
  id: string;
  // [fields]
}
```

### API Client (`frontend/src/lib/api/`)

```typescript
// [module].ts
import { apiClient } from "@/lib/api-client";

export async function getData(): Promise<DataType[]> {
  const { data } = await apiClient.get<DataType[]>("/[path]");
  return data;
}
```

**Important:** Always use `apiClient` which routes through `/api/proxy/` — never call FastAPI directly.

### Hooks (`frontend/src/hooks/`)

```typescript
// use[Feature].ts
export function use[Feature]() {
  return useQuery({
    queryKey: [...],
    queryFn: () => getData(),
    staleTime: 30_000,
  });
}
```

### Pages (`frontend/src/app/(main)/[path]/`)

| Page | File | Access Level |
|------|------|-------------|
| [Description] | `page.tsx` (server) + `[Feature]View.tsx` (client) | [roles] |

**Add to `frontend/src/lib/rbac.ts`:**
```typescript
ROUTE_PERMISSIONS["/[path]"] = [/* allowed roles */];
// and NAV_SECTIONS if visible in sidebar
```

---

## Database Migration

If new tables or columns are added:

```bash
cd backend
python -m alembic revision --autogenerate -m "[description]"
python -m alembic upgrade head
```

**Review the generated migration** before applying — autogenerate is not always correct.

---

## Testing

```bash
# Backend
cd backend && python -m pytest -q

# Frontend
cd frontend && npm run lint && npx tsc --noEmit && npm run build
```

New tests should be added in `backend/tests/` for any new service functions.

---

## Common Mistakes

| Mistake | Correct Approach |
|---------|-----------------|
| [Wrong pattern] | [Right pattern] |
| Using `Depends(CoordinatorRequired)` | Use `CoordinatorRequired` directly as default value |
| Calling FastAPI from browser JS | Use `apiClient.get('/path')` which goes via proxy |
| Missing `institution_id` filter | Always filter by `current_user.institution_id` |

---

## Checklist Before Marking Complete

- [ ] All backend tests pass
- [ ] TypeScript compiles with 0 errors
- [ ] ESLint exits 0
- [ ] Production build clean
- [ ] CHANGELOG.md updated
- [ ] PHASE_TRACKER.md updated
- [ ] Architecture doc updated if structure changed
