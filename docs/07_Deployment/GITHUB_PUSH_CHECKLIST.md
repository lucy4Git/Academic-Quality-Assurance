# AQAA — GitHub Push Checklist

**Version:** 1.0.0-rc4  
**Date:** 2026-07-04  
**Status:** Ready to push

---

## Pre-Push Verification (run once before pushing)

### 1. Secret safety
- [x] `backend/.env` is gitignored (`git check-ignore backend/.env` returns a match)
- [x] `frontend/.env.local` is gitignored (`git check-ignore frontend/.env.local` returns a match)
- [x] `git grep "sk-proj"` returns 0 matches in committed files
- [x] `git grep "sk-ant-api"` returns 0 matches in committed files
- [x] `git grep "AIza"` returns 0 matches in committed files
- [x] `git grep "OPENAI_API_KEY=sk-"` returns 0 matches in committed files
- [x] `git grep "GEMINI_API_KEY=AQ\."` returns 0 matches in committed files
- [x] Secret Safety Audit Report reviewed: `docs/07_Deployment/SECRET_SAFETY_AUDIT_REPORT.md`

### 2. Environment templates present
- [x] `.env.example` — root template (no secrets)
- [x] `backend/.env.example` — full backend template with placeholder keys
- [x] `frontend/.env.example` — frontend template

### 3. Quality gates
- [x] `python -m pytest -q` — 981 passed, 0 failures
- [x] `npx tsc --noEmit` — 0 type errors
- [x] `npm run lint` — 0 lint errors
- [x] `npm run build` — clean production build

### 4. Repository hygiene
- [x] `.gitignore` covers all secret file patterns
- [x] `.gitattributes` normalises line endings (LF)
- [x] No `__pycache__/`, `.next/`, `node_modules/` staged
- [x] No `storage/uploads/`, `storage/processed/`, `storage/reports/` staged

---

## Git Commands to Push Safely

```bash
# Step 1 — Navigate to the project root
cd "C:\Users\Staff 101\OneDrive\Desktop\AQAA"

# Step 2 — Confirm git is initialized (already done)
git status

# Step 3 — Stage everything (env files are already ignored)
git add -A

# Step 4 — Final secret scan on what's about to be committed
git grep "sk-proj"       # must return nothing
git grep "sk-ant-api"    # must return nothing
git grep "AIza"          # must return nothing

# Step 5 — Commit
git commit -m "feat: AQAA v1.0.0-rc4 — market-ready AI QA SaaS platform

- 8 AI audit agents (ADIP framework)
- Multi-agent orchestration
- AI Workspace with chat history, sources, export
- Institution Workspace with timeline and stats
- Commercial landing page
- Public registration + admin approval workflow
- Bulk ZIP document import with ADIP classification
- Vector knowledge base (TUT + UP indexed)
- Qualification Intelligence (GPA, CGPA, NQF)
- Analytics, reports (CSV/Excel/PDF)
- 981 backend tests, 0 type errors, clean build

Pilots: TUT (ICT) and UP (EBIT)"

# Step 6 — Create GitHub remote and push
git remote add origin https://github.com/<your-org>/aqaa.git
git branch -M main
git push -u origin main
```

---

## Repository Visibility Recommendation

**Start as Private.** Even though no secrets are in the committed files, the codebase contains institutional pilot data references (TUT, UP programme structures). Set visibility to Public only after stakeholder approval.

---

## Post-Push Steps

1. **Configure GitHub repository settings:**
   - Enable branch protection on `main` (require PR reviews)
   - Enable secret scanning alerts
   - Enable Dependabot alerts

2. **Add GitHub Actions CI** (optional, future sprint):
   - `pytest` on every push
   - `tsc --noEmit` + `npm run build` on every push
   - Secret scanning (GitGuardian or GitHub native)

3. **Share access** with pilot institution stakeholders (TUT, UP QA officers) as collaborators or via GitHub Teams.

4. **Tag the release:**
   ```bash
   git tag -a v1.0.0-rc4 -m "Release Candidate 4 — market-ready AI QA SaaS"
   git push origin v1.0.0-rc4
   ```
