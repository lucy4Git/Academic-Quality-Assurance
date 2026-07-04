# AI QA Assistant — User Guide

## Overview

The AI QA Assistant lets you ask natural-language questions about your institution's programmes, modules, and compliance requirements. Answers are grounded in the Institutional Knowledge Package (IKP) loaded into the Qdrant vector store.

---

## Accessing the assistant

Navigate to **AI QA Assistant** in the sidebar (visible to all staff roles; students are blocked).

---

## Development mode notice

If you see an amber banner saying **"Development mode"**, the system is using hash-based placeholder embeddings. Answers are template-generated rather than semantically retrieved. This is normal during development — the banner disappears when a real embedding model is configured.

---

## Asking questions

1. Type your question in the input box at the bottom of the page.
2. Press **Enter** or click **Ask**.
3. The assistant retrieves relevant chunks from your institution's IKP and assembles an answer.

**Example questions:**
- "What programmes does TUT offer in Engineering?"
- "What are the compliance requirements for module evidence submission?"
- "Which modules are at risk based on the last audit?"
- "What evidence documents are required for the CHE audit?"

---

## Suggested questions

When you first open the assistant (before any conversation), a grid of suggested questions appears. These are role-aware:
- **Lecturers and coordinators** see module and programme questions.
- **QA officers** see compliance and audit questions.
- **System administrators** see multi-institution questions.

Click any suggestion to submit it immediately.

---

## Source cards

Each answer includes source cards showing the IKP chunks that informed the response:
- **Entity type** (programme, module, lecturer, etc.)
- **Title** and **text excerpt** (click "Show" to expand)
- **Source document** and **relevance score**

---

## Follow-up questions

After each answer, the assistant suggests follow-up questions based on the detected intent. Click any follow-up pill to ask it immediately.

---

## Institution selector (System Admin only)

Administrators see a dropdown to select the institution before asking. You must select an institution before the Ask button activates. Each query is scoped to the selected institution — cross-institution answers are not supported in a single query.

---

## Role access

| Role | Access |
|------|--------|
| Lecturer+ | Full access |
| Student | Blocked |
