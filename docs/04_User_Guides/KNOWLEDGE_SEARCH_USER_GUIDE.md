# Knowledge Search — User Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Audience:** QA Officers, Faculty Deans, HODs, Programme Coordinators, Lecturers

---

## Overview

The Knowledge Search page allows staff to search the institutional knowledge
base using natural language queries. Results are drawn from the indexed
Institutional Knowledge Package (IKP) and include programmes, modules,
faculties, admission requirements, and campus information.

---

## Accessing Knowledge Search

1. Log in with your institution credentials.
2. In the left sidebar under **KNOWLEDGE**, click **Knowledge Search**.
3. The search page loads at `/knowledge-search`.

**Minimum role required:** Lecturer

---

## Who Can Search What

| Role | Searchable institutions |
|---|---|
| System Admin | Any active pilot institution (select from dropdown) |
| All other staff | Own institution only (automatically applied) |

Archived demo institutions (GFU, RCT) cannot be searched by anyone.

---

## Running a Search

1. Type a query in the search box.
   - Examples:
     - `What are the NQF level 6 programmes in computer science?`
     - `Module codes for first year information technology`
     - `Admission requirements for BSc Computer Science`
2. (System Admin only) Select an institution from the **Institution** dropdown.
3. Optionally select an **Entity type** to filter results to a specific kind of
   knowledge (Programme, Module, Faculty, etc.).
4. Optionally adjust **Results** (how many to return) and **Min confidence**.
5. Click **Search**.

---

## Reading Results

Each result card shows:

| Field | Description |
|---|---|
| Rank + Title | Result number and entity name |
| Entity type badge | Programme / Module / Faculty / etc. |
| Confidence badge | How reliably this record was extracted from source documents |
| Text | The full knowledge chunk text |
| Relevance % | How closely the result matches the query (hash-based in dev mode) |
| Source | The IKP source document reference |

---

## Development Mode Notice

When the system is using placeholder embeddings (dev/pilot environment), a
yellow notice appears:

> **Development mode:** Using hash-based placeholder embeddings. Results are
> ranked by hash similarity, not semantic meaning.

In this mode, results are returned but relevance ranking is not meaningful.
Contact your system administrator to confirm whether real semantic embeddings
have been configured.

---

## Filters Reference

| Filter | Options | Default |
|---|---|---|
| Entity type | All types, Programme, Module, Faculty, Department, Institution, Admission Requirement, Campus | All types |
| Results | 5, 10, 20, 50 | 10 |
| Min confidence | Any, 70%+, 85%+, 90%+ | Any |

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| "institution_code is required" error | System Admin searched without selecting an institution | Select an institution from the dropdown |
| "has not been indexed yet" error | Qdrant collection not yet built | Ask System Admin to run the indexing script |
| No results returned | Query too specific, or wrong entity type filter | Try broader keywords or set Entity type to "All types" |
| 503 Service Unavailable | Qdrant container not running | Ask System Admin to start Docker services |
