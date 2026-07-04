# Knowledge Base Documentation

This section documents AQAA's Institutional Knowledge Package (IKP) system.

## What Is the IKP?

The IKP is a version-controlled, provenance-tagged JSON package that encodes everything AQAA needs to know about an institution. It is the single source of truth for all institutional academic data.

Every record in AQAA that contains institutional knowledge must originate from an IKP.

## IKP Architecture Reference

See `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` Section 7 and the full IKP design in Phase 5.4C.

## IKP File Location

```
ikp/institutions/
  tut/              — Tshwane University of Technology
    2026/
      v1.0.0/       — Sealed version (HTML-only ICT pilot)
      v1.1.0/       — Planned: after PDF extraction
  gfu/              — Greenfield University (demo — no IKP, seeded directly)
  rct/              — Riverside College of Technology (demo — no IKP)
```

## Contents

| Document | Description | Status |
|----------|-------------|--------|
| `IKP_ARCHITECTURE.md` | Complete IKP specification (from Phase 5.4C) | ⏳ To be extracted from session |
| `IKP_JSON_SCHEMA.md` | JSON schema reference for all IKP entities | ⏳ Planned |
| `PROVENANCE_MODEL.md` | Provenance tracking specification | ⏳ Planned |
| `VERSIONING_MODEL.md` | IKP versioning rules | ⏳ Planned |
| `INGESTION_PIPELINE.md` | 9-stage data ingestion pipeline | ⏳ Planned |
| `CONFIDENCE_SCORING.md` | Confidence score calculation | ⏳ Planned |
| `TUT_PILOT_IKP.md` | TUT ICT faculty pilot data | ⏳ Planned |

## IKP Confidence Thresholds

| Score | Classification | AQAA Treatment |
|-------|---------------|---------------|
| ≥ 0.85 | Verified/High | Load immediately |
| 0.70–0.84 | Medium | Load with `pending_review` flag |
| < 0.70 | Low/Unverified | Block — quarantine |

## IKP Status by Institution

| Institution | Code | IKP Status | Version | Scope |
|-------------|------|-----------|---------|-------|
| Greenfield University (demo) | GFU | No IKP (seed data) | N/A | Full |
| Riverside College of Technology (demo) | RCT | No IKP (seed data) | N/A | Full |
| Tshwane University of Technology | TUT | v1.0.0-draft | HTML only | ICT Faculty |
