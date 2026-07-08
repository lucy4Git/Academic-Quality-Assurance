# Product Navigation Guide

## The 5 Workspaces

AQAA is organised into five primary workspaces. Everything in the platform lives inside one of these five areas.

---

### 🏠 Home (`/dashboard`)
**Access:** All authenticated users

The AI-first home page. Shows:
- **Ask AQAA** — conversational AI composer with suggested prompts
- **Quick Actions** — role-filtered shortcuts (Audit Centre, Upload Evidence, Knowledge Base, Quality Centre, Reports)
- **Health Score** — institution health tile (QA+ only)
- **Live Stats** — Modules, Programmes, Open Findings, Evidence Files (QA+ only)
- **Recent AI Activity** — last AI interactions
- **Today's Priorities** — pending tasks
- **Continue Working** — in-progress items

---

### 🧠 Workspace (`/workspace`)
**Access:** Staff (Lecturer+)

ChatGPT-style AI workspace. Shows:
- **Ask AQAA** — full-width composer for open-ended queries
- **Suggested prompts** — 6 domain-specific prompt starters
- **AI Tools** — AI QA Assistant, AI Workspace, Qualification Intelligence, Institution Workspace
- **Recent Conversations** — last 3 AI sessions
- **Pinned Documents** — saved institutional documents

---

### 📚 Knowledge (`/knowledge`)
**Access:** Staff for browsing; QA+ for acquisition/extraction

| Card | Route | RBAC |
|------|-------|------|
| Knowledge Foundation | `/knowledge/foundation` | Staff |
| Public Acquisition | `/knowledge/acquisition` | QA+ |
| Extraction Review | `/knowledge/acquisition/extraction` | QA+ |
| Semantic Search | `/knowledge-search` | Staff |
| Knowledge Graph | `/ikp-management` | QA+ |
| Documents | `/files` | Staff |

---

### ✅ Quality (`/quality`)
**Access:** Coordinator+ for most; Dean+ for compliance/accreditation; QA+ for policy

| Card | Route | RBAC |
|------|-------|------|
| Audits | `/audits` | Coordinator+ |
| Evidence | `/files` | Staff |
| Upload Evidence | `/files/upload` | Coordinator+ |
| Findings | `/findings` | Staff |
| Compliance | `/reports/compliance` | Dean+ |
| Accreditation | `/accreditation` | Dean+ |
| Programme Review | `/audits` | Coordinator+ |
| Policy Review | `/knowledge-review` | QA+ |

---

### 🏢 Administration (`/administration`)
**Access:** System Admin only

| Card | Route |
|------|-------|
| Institutions | `/institutions` |
| Users | `/users` |
| Roles | `/users` |
| Permissions | `/settings/system` |
| AI Providers | `/settings/ai-providers` |
| Monitoring | `/settings/system` |
| Scheduler | `/settings/system` |
| Logs | `/settings/system` |
| Settings | `/settings/system` |

---

## Command Palette (⌘K / Ctrl+K)

Opens from any page. Grouped into 5 sections:
1. **Navigate** — jump to any workspace
2. **AI Actions** — Ask AQAA, AI Workspace, Qualification Intelligence
3. **Knowledge** — Foundation, Acquisition, Extraction, Search
4. **Quality** — Audits, Evidence, Findings, Compliance, Accreditation
5. **Administration** — Institutions, Users, AI Providers (SA only)

Each entry is RBAC-filtered — users only see items their role permits.
