# AQAA Staging — Provisioning Tracker

**Environment:** staging (Neon / Render / Vercel)
**Last updated:** 2026-07-27

---

## Infrastructure status

| Service | Provider | Status |
|---------|----------|--------|
| PostgreSQL | Neon (free) | ✅ Live — migration at `e10000000c2 (head)` |
| Redis | Upstash (free) | ✅ Live |
| Vector store | Qdrant Cloud (free) | ✅ Live |
| Backend API | Render Free Web Service | ✅ Live — `https://aqaa-backend.onrender.com` |
| Background worker | Render | ⛔ Disabled — Render Free cannot provision worker services |
| Frontend | Vercel (free) | ✅ Live — see current deployment URL |
| Object storage | — | ⏳ Pending provider decision (`STORAGE_BACKEND=local`) |

---

## Seed scripts applied to staging

| Script | Applied | Stage in run_all.py |
|--------|---------|---------------------|
| `seed.py` | ✅ Yes | Step 1 |
| `seed_extended.py` | ✅ Yes | Step 2 |
| `seed_audit_history.py` | ✅ Yes | Step 3 |
| `seed_sa_universities.py` | ✅ Yes | Step 4 |
| `seed_institution_knowledge_foundation.py` | ✅ Yes | Step 5 |
| `seed_knowledge_acquisition_sources.py` | ✅ Yes | Step 6 |
| `seed_pilot_users.py` | ❌ Not applied | Not part of run_all.py |
| `seed_tut.py` | ❌ Not applied | Not part of run_all.py |
| `seed_up.py` | ❌ Not applied | Not part of run_all.py |

---

## User role coverage

| UserRole enum value | Seeded by run_all.py | Provisioned by staging_provision_roles.py |
|---------------------|---------------------|------------------------------------------|
| `system_admin` | ❌ | ⏳ Pending execution |
| `quality_assurance_officer` | ✅ | N/A (already present) |
| `faculty_dean` | ❌ | ⏳ Pending execution |
| `head_of_department` | ❌ | ⏳ Pending execution |
| `programme_coordinator` | ❌ | ⏳ Pending execution |
| `lecturer` | ✅ | N/A (already present) |
| `student` | ✅ | N/A (already present) |

### Roles requested but not in UserRole enum

| Requested role | Disposition |
|----------------|-------------|
| `INSTITUTION_ADMIN` | Not in UserRole enum — not provisioned |
| `INTERNAL_MODERATOR` | Not in UserRole enum — `ModerationType.INTERNAL_MODERATION` is an audit-process enum value, not a user role |
| `EXTERNAL_MODERATOR` | Not in UserRole enum — not provisioned |
| `EXTERNAL_REVIEWER` | Not in UserRole enum — not provisioned |

---

## Account inventory (source: seed files — not yet DB-verified for this session)

See `staging_inventory.py` for the database-backed version.  Run it after
setting `DATABASE_URL` to produce a live inventory.

### Tenant: Greenfield University (GFU)

| Email | Role | Active | Verified |
|-------|------|--------|----------|
| `qa.officer@gfu.ac.uk` | quality_assurance_officer | yes | yes |
| `qa.officer1@gfu.ac.uk` | quality_assurance_officer | yes | yes |
| `lecturer1@gfu.ac.uk` | lecturer | yes | yes |
| `lecturer2@gfu.ac.uk` | lecturer | yes | yes |
| `lecturer3@gfu.ac.uk` | lecturer | yes | yes |
| `lecturer.eee1@gfu.ac.uk` … `lecturer.his3@gfu.ac.uk` | lecturer | yes | yes |
| `student.bengee1@gfu.ac.uk` … `student.bahis2@gfu.ac.uk` | student | yes | yes |

*Pending provisioning:* `dean.fce@gfu.ac.uk` (faculty_dean), `hod.cs@gfu.ac.uk` (head_of_department), `coordinator.bsccs@gfu.ac.uk` (programme_coordinator)

### Tenant: Riverside College of Technology (RCT)

| Email | Role | Active | Verified |
|-------|------|--------|----------|
| `qa.officer1@rct.ac.uk` | quality_assurance_officer | yes | yes |
| `qa.officer2@rct.ac.uk` | quality_assurance_officer | yes | yes |
| `lecturer.mee1@rct.ac.uk` … `lecturer.che3@rct.ac.uk` | lecturer | yes | yes |
| `student.bengmee1@rct.ac.uk` … `student.bscche2@rct.ac.uk` | student | yes | yes |

*Pending provisioning:* `dean.fcs@rct.ac.uk` (faculty_dean), `hod.sen@rct.ac.uk` (head_of_department), `coordinator.bscsen@rct.ac.uk` (programme_coordinator)

### Cross-tenant

| Email | Role | Institution | Active | Verified |
|-------|------|-------------|--------|----------|
| `staging.admin@aqaa.internal` | system_admin | none | yes | yes |

Status: ⏳ Pending provisioning script execution

---

## Password rotation status

| Status | Detail |
|--------|--------|
| Original seeded password | `ChangeMe123!` — **must be treated as compromised** |
| Shell helper (`rotate_staging_passwords.sh`) | \\r input bug fixed in commit `119934b`; execution not yet confirmed |
| Python helper (`staging_rotate_passwords.py`) | Created 2026-07-27; cross-platform; uses `getpass`; no \\r risk |
| Rotation executed | ⏳ Pending — owner must run before granting any external access |

---

## Utilities

| Script | Purpose |
|--------|---------|
| `backend/scripts/staging_inventory.py` | Print database-backed account list (safe — no hashes) |
| `backend/scripts/staging_rotate_passwords.py` | Rotate passwords for all or selected staging users |
| `backend/scripts/staging_provision_roles.py` | Idempotent provisioner for missing RBAC roles |

---

## Next actions required (owner)

1. Run `staging_provision_roles.py` against Neon — record generated passwords in password manager.
2. Run `staging_rotate_passwords.py --all` to replace `ChangeMe123!` on all seeded accounts.
3. Run `staging_inventory.py` to produce a database-backed account list.
4. Complete QA Officer login smoke test on the deployed frontend.
5. Update `CORS_ORIGINS` on Render after Vercel URL is confirmed.
6. Decide on object storage provider (Backblaze B2 recommended).
