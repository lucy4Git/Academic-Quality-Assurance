# Streaming AI Workspace — User Guide

**Phase:** 3 Sprint 2  
**Last Updated:** 2026-07-06  
**Audience:** QA Officers, Lecturers, Programme Coordinators

---

## What's new

The AQAA AI Workspace now streams responses as they are generated, instead of waiting for the full answer to load. You will see:

- **Agent badges appear immediately** — before the answer starts, AQAA tells you which specialist agent is handling your question
- **Text streams word by word** — the answer appears progressively, like a real conversation
- **Sources appear after** — once the answer is complete, source documents and confidence scores are shown
- **Animated cursor** — a small pulsing cursor shows while AQAA is still generating

---

## How to use the AI Workspace

### 1. Open the workspace

Navigate to **AI Workspace** in the left sidebar.

### 2. Select your institution (System Admin only)

If you are a System Administrator, choose your target institution from the dropdown at the top of the left panel before asking a question.

Non-admin users are automatically scoped to their own institution.

### 3. Ask your question

Type your question in the input box at the bottom. You can ask about:

- **Audits** — "What is the compliance status of module CSC401?"
- **Evidence** — "Which modules are missing moderation reports?"
- **Accreditation** — "Is the ICT faculty ready for ECSA accreditation?"
- **Policy** — "What is the institutional policy on supplementary assessments?"
- **Reporting** — "Summarise QA status for the IT programme"

Press **Enter** or click the **Send** button.

### 4. Watch AQAA analyse

After sending, you will see:

1. **Agent badge(s)** — which specialist agent(s) AQAA selected (e.g., "Assessment Compliance Agent")
2. **Streaming answer** — text appears progressively with a blinking cursor
3. **Sources panel** — after the answer completes, relevant IKP documents are listed in the right panel with relevance scores
4. **Confidence score** — shown as a coloured bar (green = high, amber = moderate, red = low)

### 5. Use follow-up questions

Below each answer, AQAA suggests follow-up questions. Click any to ask immediately.

### 6. Explore sources

Open the **Sources & Context** panel on the right to see:
- Source documents with relevance scores
- Which agents were used
- Suggested next actions (e.g., "Run Evidence Verification Audit")

---

## Slash commands

Type `/` in the message box to see available commands:

| Command | Purpose |
|---------|---------|
| `/audit` | Analyse audit evidence for a module |
| `/policy` | Search institution policy documents |
| `/evidence` | Check module evidence status |
| `/report` | Generate a QA report |
| `/qualification` | NQF level and credit analysis |

---

## Multi-agent mode

Toggle **Multi** in the message composer to enable multi-agent mode. In this mode, AQAA dispatches multiple specialist agents simultaneously and combines their findings into a single answer. Use this for complex questions that span multiple QA domains.

In multi-agent mode, the response takes longer but is more comprehensive. Individual agent contributions are shown below the main answer.

---

## Non-streaming fallback

If the streaming connection fails (e.g., network interruption), AQAA automatically falls back to the standard non-streaming endpoint and delivers the complete answer at once. You will not see the streaming animation, but the answer content is the same.

---

## Source grounding

AQAA always searches the Institutional Knowledge Package (IKP) before generating an answer. If no relevant documents are found, AQAA will explicitly state: *"No institutional source was found for this query."* AQAA does not invent policy facts.

---

## Access control

| Role | AI Workspace | Provider Health Monitoring |
|------|-------------|---------------------------|
| Student | Not accessible | Not accessible |
| Lecturer | Full access | Not accessible |
| Programme Coordinator | Full access | Not accessible |
| Head of Department | Full access | Not accessible |
| Faculty Dean | Full access | Not accessible |
| QA Officer | Full access | Not accessible |
| System Admin | Full access (all institutions) | Accessible via Settings → AI Providers |
