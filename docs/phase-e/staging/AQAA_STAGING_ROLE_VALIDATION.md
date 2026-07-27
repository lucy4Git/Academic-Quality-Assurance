# AQAA Staging — Role Validation Record

**Environment:** staging (Neon / Render / Vercel)
**Last updated:** 2026-07-27
**Authoritative source:** `backend/app/models/enums.py` — `UserRole`

---

## Supported roles (present in UserRole enum)

| Role value | Enum name | institution_id required | Notes |
|-----------|-----------|------------------------|-------|
| `system_admin` | `SYSTEM_ADMIN` | No (nullable by design) | Cross-tenant; no institution binding |
| `quality_assurance_officer` | `QUALITY_ASSURANCE_OFFICER` | Yes | Seeded by `seed.py` + `seed_extended.py` |
| `faculty_dean` | `FACULTY_DEAN` | Yes | Not seeded by `run_all.py` |
| `head_of_department` | `HEAD_OF_DEPARTMENT` | Yes | Not seeded by `run_all.py` |
| `programme_coordinator` | `PROGRAMME_COORDINATOR` | Yes | Not seeded by `run_all.py` |
| `lecturer` | `LECTURER` | Yes | Seeded by `seed.py` + `seed_extended.py` |
| `student` | `STUDENT` | Yes | Seeded by `seed.py` + `seed_extended.py` |

RBAC hierarchy (cumulative, highest to lowest):
```
SYSTEM_ADMIN → QUALITY_ASSURANCE_OFFICER → FACULTY_DEAN →
HEAD_OF_DEPARTMENT → PROGRAMME_COORDINATOR → LECTURER → STUDENT
```

---

## Unsupported roles (not in UserRole enum)

These roles were requested for staging provisioning but do not exist in the
current AQAA data model. They are documented here rather than forced.

| Requested role | Disposition | Evidence |
|----------------|-------------|---------|
| `INSTITUTION_ADMIN` | **Not in UserRole enum** | `enums.py` contains no such value. No DB column, no RBAC entry. |
| `INTERNAL_MODERATOR` | **Not a user role** | `ModerationType.INTERNAL_MODERATION` is an audit-process enum value in `enums.py`, not a `UserRole`. Cannot be assigned to a `User`. |
| `EXTERNAL_MODERATOR` | **Not in UserRole enum** | No such value. `ModerationType.EXTERNAL_MODERATION` is audit-process only. |
| `EXTERNAL_REVIEWER` | **Not in UserRole enum** | No such value in any enum. |

If any of these roles are required for a future sprint, a migration adding the
value to `UserRole` must be authored, reviewed, and merged first. No staging
account should use an invented enum value.

---

## Accounts provisioned by `staging_provision_roles.py`

Script: `backend/scripts/staging_provision_roles.py`
Run status: ⏳ Pending owner execution

### Cross-tenant

| Email | Role | Institution | Active | Verified |
|-------|------|-------------|--------|----------|
| `staging.admin@aqaa.internal` | system_admin | none | yes | yes |

### Greenfield University (GFU)

| Email | Role | Institution | Active | Verified |
|-------|------|-------------|--------|----------|
| `dean.fce@gfu.ac.uk` | faculty_dean | GFU | yes | yes |
| `hod.cs@gfu.ac.uk` | head_of_department | GFU | yes | yes |
| `coordinator.bsccs@gfu.ac.uk` | programme_coordinator | GFU | yes | yes |

### Riverside College of Technology (RCT)

| Email | Role | Institution | Active | Verified |
|-------|------|-------------|--------|----------|
| `dean.fcs@rct.ac.uk` | faculty_dean | RCT | yes | yes |
| `hod.sen@rct.ac.uk` | head_of_department | RCT | yes | yes |
| `coordinator.bscsen@rct.ac.uk` | programme_coordinator | RCT | yes | yes |

---

## Login smoke-test log

| Date | Account | Frontend URL | Result | Notes |
|------|---------|-------------|--------|-------|
| 2026-07-27 | — | — | ⏳ Pending | Awaiting provisioning execution |

---

## Password rotation log

| Date | Method | Accounts rotated | Result |
|------|--------|-----------------|--------|
| — | `staging_rotate_passwords.sh` (shell) | — | ⛔ Not confirmed — `\r` input bug blocked execution |
| — | `staging_rotate_passwords.py` (Python, `getpass`) | — | ⏳ Pending owner execution |

`ChangeMe123!` must be considered compromised until rotation is confirmed.

---

## Full role coverage status

| Role | Coverage |
|------|----------|
| system_admin | ⏳ Pending provisioning |
| quality_assurance_officer | ✅ Seeded (GFU × 2, RCT × 2) |
| faculty_dean | ⏳ Pending provisioning |
| head_of_department | ⏳ Pending provisioning |
| programme_coordinator | ⏳ Pending provisioning |
| lecturer | ✅ Seeded (GFU × 24, RCT × 24) |
| student | ✅ Seeded (GFU × 14, RCT × 16) |
