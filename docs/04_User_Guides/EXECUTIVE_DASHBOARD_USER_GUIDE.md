# Executive Dashboard — User Guide

**Version:** 2.0.0-sprint2  
**Audience:** All AQAA users  
**Last Updated:** 2026-07-05

---

## What is the Executive Dashboard?

The AQAA Executive Dashboard is your AI-powered command centre for academic quality assurance. It gives you a real-time view of your institution's quality health, outstanding priorities, and AI-generated insights — all on a single screen.

---

## Dashboard Sections

### Hero — Your Personalised Welcome

At the top of the dashboard you will see:

- **Time-of-day greeting** — Good morning / afternoon / evening
- **Institution badge** — Shows your institution (TUT, UP, or platform-wide for admins)
- **Role badge** — Your current role
- **Institution Health Score** — An animated circular gauge showing overall QA health (0–100)
- **AI Summary** — A one-sentence status from AQAA
- **Quick action buttons** — Ask AQAA, Start Audit, Upload Folder, Generate Report

### AI Suggestions

Rounded pill buttons showing context-aware recommendations. Click any to jump directly to that action. Available suggestions depend on your role.

### Ask AQAA — Mini Widget

A small AI assistant panel where you can:
1. Type any quality assurance question and press Send
2. Click a suggested prompt to open the AI assistant with it pre-filled
3. Click **Open Full AI Workspace** for the complete AI experience

### AI Insights Today

Six animated counters showing today's AI activity:
- Documents Analysed
- Audits Completed
- Evidence Indexed
- Reports Generated
- Risks Detected
- Recommendations Created

### Today's Priorities

A list of outstanding tasks, colour-coded by urgency:
- 🔴 **HIGH** — Requires immediate attention (e.g. missing moderation report)
- 🟡 **MEDIUM** — Should be addressed this week
- 🟢 **LOW** — On the horizon

Click **Review now** or the action button on any task to navigate directly.

> Visible to Programme Coordinators and above.

### Recent AI Activity

A real-time timeline of what AQAA's AI agents have been doing — audits triggered, evidence indexed, reports generated, and risks flagged — with timestamps.

### Institution Health

A radial chart showing five quality dimensions:
| Dimension           | What it measures                          |
|---------------------|-------------------------------------------|
| Overall             | Composite institutional health score      |
| Compliance          | Policy and regulatory adherence           |
| Evidence Completeness | How much required evidence is uploaded  |
| Assessment Quality  | Quality of submitted assessments          |
| Moderation Status   | Moderation report completion rate         |

Colour coding: Green ≥ 85% · Amber 70–84% · Red < 70%

> Visible to QA Officers and above.

### Faculty Overview

Cards for each faculty showing:
- **Health %** — Overall faculty quality score
- **Modules** — Number of active modules
- **Missing** — Missing evidence items
- **Risks** — Open risk flags
- **Sparkline** — 6-period health trend

Click any faculty card to manage that faculty.

> Visible to Faculty Deans and above.

### Knowledge Base & Services

Status of all backend systems powering AQAA:
- **Qdrant** — AI vector knowledge store
- **Redis** — Caching layer
- **Postgres** — Primary database
- **OpenAI** — AI provider (GPT-4o)
- **Ollama** — Local AI fallback
- **MinIO** — Document storage

An animated green pulse means the service is healthy.

---

## Keyboard Shortcuts

| Shortcut    | Action                          |
|-------------|---------------------------------|
| `Ctrl+K`    | Open Command Palette            |
| `Escape`    | Close Command Palette           |

---

## Tips

- The AI Summary updates based on your institution's current data. If it says "modules require attention", click **Start Audit** to investigate.
- Clicking any **Today's Priority** item takes you directly to the workflow or upload screen.
- The **Ask AQAA** widget supports natural language — try "Which modules have incomplete evidence?" or "Show me last quarter's compliance summary".
- The Health Score is updated each time audits are completed. Run regular audits to keep it accurate.
