# ADR-0007 — Documentation-Driven Development

**Status:** Accepted  
**Date:** 2026-06-29  
**Deciders:** Phase 5.4D architecture session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

AQAA has been developed across many separate development sessions. Each session builds on prior work but without persistent documentation, critical decisions had to be rediscovered repeatedly:

- The ShadCN `@base-ui/react` incompatibility with `asChild` prop was discovered in multiple sessions
- The `Depends()` double-wrap bug in FastAPI routes was fixed and then reintroduced
- The `Faculty.__tablename__` override needed to be re-explained
- The `api-client.ts` baseURL bug was introduced after being fixed
- Data provenance gaps were only discovered in Phase 5.4A, months after data was loaded

These repeated discoveries consume development time and introduce regression risk. More critically, as the platform grows toward production deployment, new contributors (human or AI) need a reliable reference for every design decision.

The project has also grown beyond what can be held in a single context window. Documentation is the only durable memory that persists across sessions.

---

## Decision

AQAA adopts **Documentation-Driven Development** as a core engineering discipline.

This means:

1. **`docs/` is a first-class project artefact** — as important as `backend/` and `frontend/`
2. **Every feature ships with documentation** — architecture entry, changelog entry, and (if architectural) an ADR
3. **`CLAUDE_DEVELOPMENT_STANDARD.md`** is the engineering constitution — all sessions begin by reading it
4. **`AQAA_MASTER_ARCHITECTURE.md`** is the single source of truth — never implement anything that contradicts it without updating it first
5. **ADRs are immutable once accepted** — decisions are not silently changed; new ADRs supersede old ones
6. **No phase is closed without documentation** — all quality gates must pass (tests + lint + build) AND all documentation must be updated

The `docs/` directory is structured into 14 sections:
```
00_Project/      — Master docs, decisions, changelog, roadmap
01_Architecture/ — System architecture documents
02_Implementation/ — Implementation guides
03_Developer_Guides/ — Developer onboarding and guides
04_User_Guides/  — User-facing documentation
05_Testing/      — Test plans and strategies
06_Administration/ — Admin operations
07_Deployment/   — Deployment procedures
08_API/          — API reference
09_AI/           — AI agent documentation
10_Knowledge_Base/ — IKP architecture and data
11_Reference/    — Quick reference cards
12_Decisions/    — Architecture Decision Records
13_Research/     — Research and investigation reports
```

---

## Consequences

### Positive
- Critical decisions are recorded durably and don't need to be rediscovered
- New contributors (human or AI) can onboard via documentation without needing session history
- Regressions are preventable — documented constraints are enforceable
- The project's intellectual value is captured, not locked in session context
- Documentation gaps are visible — undocumented features are identifiable
- The engineering standard (`CLAUDE_DEVELOPMENT_STANDARD.md`) provides a consistent baseline for all sessions

### Negative
- Writing documentation takes time — every phase now has an additional documentation deliverable
- Documentation can go stale if not maintained — requires discipline to keep up to date
- The `docs/` directory adds to the repository size

### Neutral
- Quality gates now include documentation checks (not just test/lint/build)
- `PHASE_TRACKER.md` maintains a visible record of documentation debt per phase
- Subsystem template ensures consistent documentation structure

---

## Alternatives Considered

### Alternative 1 — Comments in Code Only
Document all decisions in code comments and docstrings.

**Rejected because:** Code comments do not capture context, rationale, or alternatives considered. They cannot be searched across the full project. They are deleted when code is refactored. They are not readable by non-engineers. Architecture decisions need a dedicated, durable artefact type.

### Alternative 2 — External Wiki
Use Confluence, Notion, or GitHub Wiki for documentation.

**Rejected because:** External wikis are separated from the codebase and can drift out of sync. They require separate authentication and tooling. For a standalone project built in a single repository, co-located documentation in `docs/` is the most durable and accessible format.

### Alternative 3 — No Formal Documentation (Rely on Context)
Continue as before — relying on session context and CLAUDE.md for institutional memory.

**Rejected because:** Phase 5.4A demonstrated the consequences — unexplained database records, lost provenance, repeated bug fixes. CLAUDE.md context is ephemeral (lost between sessions if context overflows). Documentation in `docs/` is permanent.

---

## Implementation Notes

Document update obligations:

| Event | Required Update |
|-------|----------------|
| New feature | `CHANGELOG.md` + section README in relevant `docs/` directory |
| Bug fix | `CHANGELOG.md` + `LESSONS_LEARNED.md` if non-trivial |
| Architecture change | `AQAA_MASTER_ARCHITECTURE.md` + new ADR |
| Phase completion | `PHASE_TRACKER.md` + `CHANGELOG.md` |
| New API endpoint | `docs/08_API/` |
| New AI agent | `docs/09_AI/` |

---

## References

- `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` — Rules 3, 4, 5
- `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md`
- `docs/00_Project/LESSONS_LEARNED.md` — LL-0007, LL-0009 (motivated this decision)
