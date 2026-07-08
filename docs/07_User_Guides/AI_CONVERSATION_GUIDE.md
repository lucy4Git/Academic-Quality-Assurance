# AI Workspace — Conversation Guide

**AQAA v4.0 · Phase 4 Wave 2**

---

## Getting Started

The AI Workspace is your primary interface to AQAA's institutional intelligence. It reasons across your institution's complete knowledge base — policies, programmes, modules, evidence, audit findings, and accreditation records.

### Opening the Workspace

Navigate to **Workspace → AI Workspace** in the left sidebar, or click the AI Workspace link in the topbar. The workspace opens with a three-panel layout:

- **Left** — Conversation history and search
- **Centre** — Your conversation with the AI
- **Right** — Live context: grounding score, knowledge sources, agents

---

## Starting a Conversation

Type your question in the composer at the bottom and press **Enter** (or click the blue Send button).

**Example questions:**

```
What programmes does TUT offer in the ICT faculty?
Which modules are missing moderation reports this semester?
Compare the credit structure of BSc CS against NQF Level 7 requirements.
Generate an accreditation readiness summary for the Engineering faculty.
What is the institution's policy on supplementary assessments?
```

The AI automatically routes your question to the most appropriate specialist agent.

---

## Slash Commands

Type `/` to open the command menu:

| Command | What it does |
|---------|-------------|
| `/new` | Start a fresh conversation |
| `/audit` | Frame your question as an audit analysis |
| `/policy` | Search institutional policies |
| `/module` | Query module information |
| `/programme` | Review programme quality |
| `/evidence` | Check module evidence status |
| `/finding` | Search audit findings |
| `/report` | Generate a quality report |
| `/qualification` | NQF/credit analysis |
| `/help` | Show this command list |

Use arrow keys to navigate, Enter or Tab to apply.

---

## Understanding Responses

### Grounding Score (right panel)

Every AI response is grounded against your institution's knowledge base. The **Grounding Score** shows how well-evidenced the response is:

| Score | Meaning |
|-------|---------|
| 80–100% (green) | Fully grounded in institutional knowledge |
| 50–79% (amber) | Partially grounded; some claims inferred |
| 0–49% (red) | Low confidence; limited institutional sources found |

A "no sources found" warning appears when the question falls outside the knowledge base. Uploading more evidence improves future scores.

### Agent Badge

Below the AQAA avatar you'll see which specialist agent handled your query:

- **QA General Assistant** — General quality assurance questions
- **Audit Summary** — Audit evidence and compliance analysis
- **Evidence Agent** — Module evidence status
- **Reporting Agent** — Report generation
- **Qualification Agent** — NQF and credit framework analysis

### Citations

Inline numbered chips (e.g. `①`) appear where the AI drew from a specific source. Hover over a chip to see:
- Source title
- Entity type (policy, programme, module, etc.)
- Relevance percentage
- Source snippet

### Follow-up Suggestions

After each response, suggested follow-up questions appear below the message. Click any to continue the conversation in that direction.

---

## Managing Conversations

### New Conversation

Click **+ New conversation** in the left sidebar, or type `/new` in the composer.

### Search Conversations

Use the search box at the top of the left sidebar to filter conversations by title.

### Pin a Conversation

Hover over a conversation in the history list and click the **Pin** icon to keep it at the top. Pins are saved to your browser.

### Delete a Conversation

Hover over a conversation and click the **Delete** (trash) icon.

---

## Exporting Responses

Hover over any AI response to see the action toolbar:

| Action | Result |
|--------|--------|
| **Copy** | Copies the plain response text to clipboard |
| **Export .md** | Downloads a Markdown file with the response and citations |
| **Regenerate** | Re-runs the same question for a fresh response |

---

## Admin Features

System Administrators see an **Institution** dropdown in the conversation sidebar. Select a specific institution to scope the AI's knowledge context. Without a selection, the question is sent without institution context.

---

## Tips for Better Responses

1. **Be specific** — "What evidence is missing from CSC401?" works better than "What's missing?"
2. **Name the entity** — Include module codes, programme names, or faculty names
3. **Use slash commands** — `/audit` or `/policy` helps the AI route to the right agent
4. **Ask follow-ups** — The AI maintains context across messages in the same conversation
5. **Check grounding** — A low score means your institution needs more knowledge uploaded

---

## Context Panel

The right panel updates after every AI response:

| Section | Contents |
|---------|---------|
| **Grounding Score** | SVG donut gauge + status label |
| **Citations** | Numbered knowledge references with relevance % |
| **Knowledge Sources** | Entity type + confidence for each retrieved chunk |
| **Agents** | Which agents were invoked (with checkmarks) |
| **Next Actions** | Suggested tasks that link to relevant AQAA pages |

Hide/show the panel with the **Hide context** / **Show context** button in the topbar.
