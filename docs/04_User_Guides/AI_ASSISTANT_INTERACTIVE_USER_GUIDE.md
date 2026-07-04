# AI QA Assistant — Interactive User Guide

## Overview

The AI QA Assistant is an interactive, source-grounded AI agent that helps Quality Assurance Officers, Faculty Deans, Programme Coordinators, and Lecturers understand compliance status, audit findings, policies, and accreditation requirements for their institution.

Unlike a search engine, the assistant reasons over your institution's live knowledge base and answers in natural language, citing the specific source documents it used.

---

## Getting started

Navigate to **AI Assistant** in the left sidebar.

### Selecting an agent mode

Choose a mode from the dropdown in the header before asking your first question. Each mode gives the AI a different focus area:

| Mode | Best for |
|------|----------|
| QA Assistant | General quality assurance questions |
| Policy Assistant | Institutional policies and regulatory frameworks |
| Audit Assistant | Module audit findings and compliance analysis |
| Evidence Assistant | Evidence portfolio completeness and upload requirements |
| Accreditation Assistant | Accreditation body requirements and readiness |
| Qualification Assistant | NQF levels, credit values, and qualification standards |
| Reporting Assistant | Interpreting compliance reports and trend data |

### Asking a question

Type your question in the input box and press **Enter** or click **Ask**. The assistant responds in seconds.

**Example questions:**
- "Which modules in the Faculty of Engineering are at risk this semester?"
- "What evidence does the moderator need to see for assessment compliance?"
- "Summarise the outstanding audit findings for Module ENG301."
- "What are the HEQC requirements for programme self-evaluation?"

### Using suggested questions

When the chat is empty, suggested questions appear based on your institution's current state. Click any suggestion to submit it immediately.

---

## Understanding responses

### Confidence score

Each assistant response displays a confidence percentage:

- **70%+** (green) — the answer is well-supported by retrieved knowledge chunks
- **40–69%** (amber) — partial support; verify against source documents
- **Below 40%** (red) — limited matching context; treat as indicative only

### Source cards

Below each response you'll see the source documents the AI cited. Click **Show** to expand any source and read the exact text it used. Sources include the entity type, document name, and relevance score.

### Follow-up questions

After each response, the assistant suggests relevant follow-up questions. Click any to continue the conversation without typing.

---

## Chat sessions

### Creating a session

Click **+ New chat** in the left sidebar. Sessions persist your conversation history so you can return to a previous analysis later.

### Switching sessions

Click any session in the sidebar to load its history.

### Deleting a session

Hover over a session in the sidebar and click the **✕** button that appears. This soft-deletes the session (history is preserved in the database but no longer shown).

### Clearing the current chat

Click **✕ Clear** in the header to clear the in-memory view without deleting the session.

---

## Regenerating a response

Click **↻ Regenerate** in the header to re-ask the last question. Use this if the response seemed incomplete or you want to see if a different context retrieval produces a better answer.

---

## Development mode notice

If you see an amber banner reading **"Development mode: responses use placeholder embeddings"**, the backend is running with `AI_PROVIDER=LOCAL_DEV`. Responses are template-based, not AI-generated. Contact your system administrator to configure a live AI provider.

---

## Institution context (admin only)

System administrators must select an institution from the dropdown in the header before asking questions. Non-admin users are automatically locked to their own institution — no selection required.

---

## Role access

| Role | Access |
|------|--------|
| System Admin | Full access, must select institution |
| QA Officer | Full access, locked to own institution |
| Faculty Dean | Full access, locked to own institution |
| Head of Department | Full access, locked to own institution |
| Programme Coordinator | Full access, locked to own institution |
| Lecturer | Full access, locked to own institution |
| Student | No access |

---

## Tips for better answers

- **Be specific.** "What are the assessment compliance issues in ENG301?" gives better results than "What are the problems?"
- **Name the module or programme.** The assistant retrieves knowledge relevant to specific entities.
- **Use the right mode.** Asking accreditation questions in Audit Assistant mode may produce less focused answers.
- **Follow the sources.** If a source card shows a low relevance score, treat the answer with caution and verify directly.
