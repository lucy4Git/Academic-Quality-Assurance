# AQAA Deployment Readiness Checklist

**Version:** 1.0.0-rc4  
**Date:** 2026-07-04  
**For:** RC4 → Production deployment

Complete every item before go-live. Items are grouped by who is responsible.

---

## 1. Secret Safety (Engineering)

- [ ] Run GitHub secret scan on entire repository history (`git log --all`)
- [ ] Confirm `backend/.env` is in `.gitignore` and NOT committed
- [ ] Confirm `frontend/.env.local` is in `.gitignore` and NOT committed
- [ ] Rotate `SECRET_KEY` — generate a new 64-char random hex: `python -c "import secrets; print(secrets.token_hex(64))"`
- [ ] Rotate any API keys that may have appeared in git history
- [ ] Confirm no hardcoded credentials in source files

## 2. Environment Configuration (Engineering)

### Backend (`backend/.env` in production)
- [ ] `APP_ENV=production`
- [ ] `DEBUG=false`
- [ ] `SECRET_KEY=<new-strong-random-key>`
- [ ] `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/aqaa_prod`
- [ ] `REDIS_URL=redis://host:6379/0`
- [ ] `QDRANT_URL=http://host:6333`
- [ ] `CORS_ORIGINS=https://aqaa.yourdomain.ac.za`
- [ ] `AI_PROVIDER=OPENAI` (or ANTHROPIC/OLLAMA)
- [ ] `OPENAI_API_KEY=<key>` (if using OpenAI)
- [ ] `ANTHROPIC_API_KEY=<key>` (if using Anthropic)

### Frontend (`frontend/.env.local` in production)
- [ ] `NEXT_PUBLIC_API_BASE_URL=https://api.aqaa.yourdomain.ac.za`

## 3. Database (DBA / Engineering)

- [ ] PostgreSQL 15+ provisioned
- [ ] Database `aqaa_prod` created with UTF-8 encoding
- [ ] DB user with limited privileges (not superuser)
- [ ] All migrations applied: `python -m alembic upgrade head`
- [ ] Verify migration state: `python -m alembic current` → should show `d5e6f7a8b9c0`
- [ ] Seed data loaded: `python ../database/seed_data/run_all.py`
- [ ] Automated daily backups scheduled (`pg_dump` or managed backup)
- [ ] Backup restore tested

## 4. Vector Store (Engineering)

- [ ] Qdrant provisioned (Docker or managed)
- [ ] TUT knowledge collection indexed (196 chunks)
- [ ] UP knowledge collection indexed (28 chunks)
- [ ] Qdrant data directory volume-mounted for persistence
- [ ] Qdrant backup strategy documented

## 5. Infrastructure (DevOps)

- [ ] Docker Compose or Kubernetes manifests reviewed for production
- [ ] SSL/TLS termination configured (nginx/traefik/load balancer)
- [ ] Health check endpoint verified: `GET /health` returns `{"status":"ok"}`
- [ ] Backend auto-restart on crash (restart policy: always)
- [ ] Log aggregation configured (stdout → Loki/CloudWatch/ELK)
- [ ] Alerting on health check failures
- [ ] Resource limits set (CPU/memory) on all containers

## 6. Security (Security Review)

- [ ] All endpoints behind authentication (no anonymous access to data)
- [ ] JWT `SECRET_KEY` is unique and not shared with other systems
- [ ] CORS restricted to production frontend domain only
- [ ] File upload max size confirmed (`MAX_UPLOAD_SIZE_MB=50`)
- [ ] Storage backend configured (`STORAGE_BACKEND=local` or S3)
- [ ] Rate limiting considered for `/auth/token` and `/auth/login`
- [ ] SQL injection: confirmed — no raw SQL strings in codebase
- [ ] XSS: confirmed — Next.js escapes by default; no `dangerouslySetInnerHTML`

## 7. User Accounts (Admin / Pilot Coordinators)

- [ ] All seeded user passwords changed from `ChangeMe123!`
- [ ] System admin account has a strong unique password
- [ ] QA officer accounts configured for TUT and UP
- [ ] Demo/archived institution accounts (GFU, RCT) disabled or removed if not needed
- [ ] MFA considered for admin accounts (future enhancement)

## 8. Frontend Build (Engineering)

- [ ] `npm run build` exits 0 — ✅ confirmed
- [ ] `npx tsc --noEmit` exits 0 — ✅ confirmed
- [ ] `npm run lint` exits 0 — ✅ confirmed
- [ ] Production build deployed to static hosting or Node.js server
- [ ] `NEXT_PUBLIC_API_BASE_URL` points to production API

## 9. Backend Tests (Engineering)

- [ ] `python -m pytest -q` → 884 passed — ✅ confirmed
- [ ] No test failures or errors
- [ ] Test suite runs in CI (if CI configured)

## 10. Pilot Onboarding (Pilot Coordinators)

- [ ] TUT QA officers briefed on the platform
- [ ] UP QA officers briefed on the platform
- [ ] User guide shared with pilot users
- [ ] Qualification Intelligence advisory disclaimer communicated to all users
- [ ] AI provider disclaimer communicated (LOCAL_DEV vs live AI)
- [ ] Support/feedback channel established

## 11. Documentation (Engineering)

- [ ] `README.md` is up to date — ✅ v1.0.0-rc1
- [ ] `CHANGELOG.md` has v1.0.0-rc1 entry — ✅
- [ ] Deployment guide available: `docs/07_Deployment/DEPLOYMENT_READINESS_CHECKLIST.md`
- [ ] User guides available: `docs/04_User_Guides/`
- [ ] Admin guide available: `docs/06_Administration/`

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Engineer | | | |
| Security Reviewer | | | |
| QA/Pilot Coordinator (TUT) | | | |
| QA/Pilot Coordinator (UP) | | | |
| Project Owner | | | |
