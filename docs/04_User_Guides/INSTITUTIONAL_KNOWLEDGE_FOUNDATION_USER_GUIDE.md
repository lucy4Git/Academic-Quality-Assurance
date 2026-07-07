# Institutional Knowledge Foundation — User Guide

## What it is

A view of your institution's structured knowledge — campuses, faculties,
departments, programmes, qualifications, modules, policies, documents,
accreditations and contacts — with a clear indication of how trustworthy each
record is.

## Data trust labels

| Label | Meaning |
|-------|---------|
| **Public verified** (green) | From official public sources (university sites, DHET, CHE, SAQA). |
| **Needs review** (amber) | Publicly known but unconfirmed / may be outdated. |
| **Synthetic demo** (blue) | Realistic placeholder data — **not** real internal data. |
| **Customer data** (purple) | Real data your institution has uploaded. Never overwritten. |

> Synthetic demo data exists only so the platform has a working knowledge graph
> to demonstrate features. It must never be treated as authoritative.

## Knowledge Foundation page (`/knowledge/foundation`)

- **System Admins** pick any of the 26 universities from the dropdown.
- **Other staff** automatically see their own institution.
- Count cards show how many records exist per entity type.
- The provenance bar shows the trust mix.
- A **Ready for RAG** badge appears when more than half the records are verified
  or under review (i.e. not purely synthetic).

## Institution Profile page (`/institution/profile`)

Shows public details, campuses, public contacts and accreditations for your
institution. Students see only public information.

## Who can see what

- Students: public institution profile only.
- Lecturer and above: coverage, policies, documents, accreditations for their
  own institution.
- System Admin: all institutions plus the platform-wide overview.
