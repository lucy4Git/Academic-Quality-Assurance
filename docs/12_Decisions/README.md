# Architecture Decision Records (ADRs)

This directory contains all Architecture Decision Records for AQAA.

## What Is an ADR?

An ADR documents a significant architectural decision, including its context, the decision made, and the consequences. ADRs are **immutable once accepted** — to change a decision, create a new ADR that supersedes the old one.

## ADR Registry

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-0001 | Standalone System | Accepted | 2026-06-11 |
| ADR-0002 | Multi-Tenant Architecture | Accepted | 2026-06-11 |
| ADR-0003 | TUT Pilot Institution | Accepted | 2026-06-25 |
| ADR-0004 | Institutional Knowledge Package | Accepted | 2026-06-29 |
| ADR-0005 | AI-First Hybrid Architecture | Accepted | 2026-06-11 |
| ADR-0006 | Provenance and Versioning | Accepted | 2026-06-29 |
| ADR-0007 | Documentation-Driven Development | Accepted | 2026-06-29 |
| ADR-0008 | Academic Document Intelligence Platform | Accepted | 2026-06-29 |

## Creating a New ADR

1. Copy `ADR-TEMPLATE.md` to `ADR-XXXX-Short-Title.md` (next sequential number)
2. Fill in all sections
3. Set status to `Proposed`
4. Get review
5. Set status to `Accepted`
6. Add to the registry above
7. Reference in `CHANGELOG.md` and `PROJECT_DECISIONS.md`

## ADR Numbering

ADRs are numbered sequentially starting from 0001. Never reuse a number.
