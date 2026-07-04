# ADR-0001 — AQAA Is a Standalone System

**Status:** Accepted  
**Date:** 2026-06-11  
**Deciders:** Project lead  
**Supersedes:** None  
**Superseded by:** —

---

## Context

The developer's machine contains multiple active software projects, including an MSc Academic Intelligence System, RIAE (Research and Innovation Agent Environment), a Lecturer Support Agent, PersonalOS, and other systems. These projects share the same development environment and may share some conceptual overlap in domain (higher education, AI, data management).

AQAA (Academic Quality Assurance Agent) is being built as a purpose-built enterprise platform for academic quality assurance — a distinct commercial product. There is a risk that, across multiple development sessions, patterns, schemas, models, or conventions from other projects could be inadvertently introduced into AQAA, creating:

- Architectural pollution (foreign patterns that don't suit AQAA's design)
- Data model corruption (models optimised for different domains)
- Naming convention confusion
- Security assumptions from other systems that don't apply here
- Dependency on code that is under active development in another project

---

## Decision

AQAA is and will remain a completely standalone project. It has no relationship to any other project on this machine or in this organisation. This means:

1. No code, schemas, models, types, hooks, routes, or conventions are imported from or shared with any other project
2. All dependencies are explicitly declared in `backend/requirements.txt` and `frontend/package.json`
3. Every development session begins with reading `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` which contains this constraint as Rule 1
4. Any future integration with an external system requires a new ADR explicitly authorising it

---

## Consequences

### Positive
- AQAA maintains architectural integrity as a standalone commercial product
- No cross-project contamination risks
- The codebase can be extracted and deployed independently at any time
- Clear IP ownership — all AQAA code is purpose-built for this platform

### Negative
- No code reuse from other projects, even for genuinely generic utilities
- Slightly more initial work to build utilities that might exist elsewhere

### Neutral
- This ADR must be cited in `CLAUDE_DEVELOPMENT_STANDARD.md` as a permanent constraint

---

## Alternatives Considered

### Alternative 1 — Shared Utility Library
Build a shared utility library for common patterns (auth, RBAC, file storage) and use it across AQAA and other projects.

**Rejected because:** Shared libraries create tight coupling between projects. AQAA's commercial viability depends on it being deployable independently. Shared libraries would create hidden dependencies and make the codebase harder to reason about.

### Alternative 2 — Monorepo with Clear Boundaries
Place all projects in a monorepo with explicit package boundaries.

**Rejected because:** The projects have fundamentally different domains, tech stacks, and deployment targets. A monorepo would add tooling complexity without meaningful benefit. The simplest, most reliable isolation is complete project separation.

---

## References

- `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` — Rule 1
- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0001
- `CLAUDE.md` — Project identity section
