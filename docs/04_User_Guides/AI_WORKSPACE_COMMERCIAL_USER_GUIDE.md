# AI Workspace — User Guide

**Version:** 2.0.0-sprint3  
**Audience:** All authenticated AQAA users (lecturer and above)  
**Last Updated:** 2026-07-05

---

## What is the AI Workspace?

The AQAA AI Workspace is a full-featured conversational interface for academic quality assurance. It works like Claude or ChatGPT — but with full knowledge of your institution's modules, programmes, policies, and evidence — and can automatically engage multiple specialist QA agents on complex questions.

Navigate to **AI Workspace** from the sidebar under **AI ASSISTANT**.

---

## Layout Overview

The workspace has three panels:

| Panel | Purpose |
|-------|---------|
| **Left** | Start new conversations, browse session history, quick links |
| **Centre** | Write messages, read AQAA responses, see agent thinking |
| **Right** | View source documents, agents used, suggested next actions |

The right panel can be toggled open or closed with the **Sources** button in the centre topbar.

---

## Starting a Conversation

### New conversation
Click **New conversation** at the top of the left panel. AQAA clears the thread and starts fresh.

### Typing a question
Click the input box at the bottom of the centre panel and type your question in plain language. Press **Enter** to send, or **Shift+Enter** for a new line.

### Using suggestion cards
When you open a new conversation, six suggestion cards appear. Click any card to send that question immediately.

---

## Understanding AQAA's Response

Each AQAA answer includes:

- **Agent badges** — which specialist agent(s) handled your question (e.g. Evidence, Accreditation, Assessment)
- **Answer text** — the response in plain language
- **Confidence bar** — how confident the system is (green ≥ 70%, amber ≥ 45%, red < 45%)
- **Source chips** — the documents consulted (up to 4 shown; see the right panel for all)
- **Provider badge** — which AI model generated the answer (e.g. OpenAI · gpt-4o)

---

## Slash Commands

Type `/` anywhere in the input to open the command menu:

| Command | Purpose |
|---------|---------|
| `/audit` | Frame your question as an audit analysis |
| `/policy` | Search institutional policy documents |
| `/evidence` | Check module evidence completeness |
| `/report` | Generate a QA report |
| `/qualification` | Analyse NQF credits or GPA calculations |

Select a command from the menu (or keep typing to filter), then complete your question after the command label.

---

## Multi-Agent Mode

By default, AQAA automatically selects the best single agent for your question. For complex, cross-cutting queries, switch to **Multi-agent mode**:

1. Click the **Auto** pill button next to the send button — it turns purple and shows **Multi**
2. Send your question
3. AQAA engages multiple agents simultaneously and merges their answers into one response
4. Agent contribution cards appear below the response showing each agent's confidence and summary

Use multi-agent mode for questions like:
- "Generate a full quality review of the ICT faculty covering assessment, evidence, and accreditation readiness"
- "Which modules need the most attention before the HEQSF visit?"

---

## Source Panel (Right Panel)

The right panel shows context for the last AQAA response:

### Source documents
Each source card shows:
- Document title and entity type (module, programme, policy, etc.)
- Relevance score (how closely it matches your question)
- A text snippet from the document

**Actions on each source:**
- **Search** — opens Knowledge Search pre-filtered to that document title
- **Cite** — copies the document reference to your clipboard

### Agents used
Cards showing each specialist agent that contributed to the response.

### Suggested actions
Quick links to take action on AQAA's response, e.g. "Create audit", "Generate report", "Upload missing evidence".

---

## Conversation History

All conversations are saved automatically. The left panel lists your recent sessions with:
- Session title (from the first question)
- Message count

**To revisit a session:** click it in the list. AQAA loads the session context.  
**To delete a session:** hover over it and click the trash icon.

---

## Exporting Answers

Click the **Export** button below any AQAA response to download the answer as a `.txt` file — useful for pasting into reports or sharing with colleagues.

---

## Message Actions

On any AQAA response:

| Button | Action |
|--------|--------|
| **Copy** | Copies the full response text to clipboard |
| **Export** | Downloads the response as a `.txt` file |

---

## Follow-up Questions

After each response, AQAA suggests up to three follow-up questions as pill buttons. Click any to send it immediately without retyping.

---

## Institution Context

### For lecturers, coordinators, deans, QA officers
Your institution is set automatically. You will see a badge (e.g. **TUT** or **UP**) in the left sidebar confirming which workspace you are in. AQAA only uses knowledge and evidence from your institution.

### For system administrators
An institution selector appears in the left sidebar. You must choose an institution before sending a question — the workspace is blocked if no institution is selected (a warning badge appears in the topbar).

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line in message |
| `/` | Open slash command menu |
| `Escape` | Close slash command menu |
| `Ctrl+K` | Open global Command Palette |

---

## Tips

- **Be specific.** "Which modules in the ICT faculty are missing moderation reports for Semester 1 2026?" gets a better answer than "Show me missing documents."
- **Use `/evidence` for compliance checks.** The Evidence agent has full visibility of uploaded module folders.
- **Use `/report` to draft Senate summaries.** The Reporting agent formats its output as a structured QA report.
- **Use Multi-agent mode before accreditation visits.** It combines Evidence, Accreditation Readiness, and Outcome Alignment agents in a single response.
- **Check the confidence bar.** A low confidence score (red) means AQAA has limited evidence in the knowledge base — consider uploading more documents.
- **Click source cards.** Opening a source in Knowledge Search shows the full document and its provenance.
- **Clear chat to start fresh.** The "Clear chat" link in the composer footer resets the thread without creating a new session.
