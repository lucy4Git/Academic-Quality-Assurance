# IKP Management — User Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Audience:** System Administrators, Quality Assurance Officers

---

## Overview

The IKP Management page gives authorised users a structured view of the
Institutional Knowledge Packages (IKPs) that underpin AQAA's AI capabilities.

You can:
- See which IKP packages are loaded for each pilot institution
- Inspect individual knowledge chunks
- Check whether the Qdrant vector index is up to date
- Trigger a re-index (Admins only)
- Create a Knowledge Review batch directly from IKP content

---

## Accessing IKP Management

1. Log in with a System Admin or QA Officer account.
2. In the left sidebar under **KNOWLEDGE**, click **IKP Management**.
3. The page loads at `/ikp-management`.

**Minimum role required:** Quality Assurance Officer

---

## Who Sees What

| Role | Packages visible | Re-index | Create batch |
|---|---|---|---|
| System Admin | TUT + UP | Yes | Yes |
| QA Officer | Own institution only | No | Yes (if extraction available) |
| All others | — (access denied) | — | — |

---

## Package Cards

Each IKP package is shown as a card with:

| Field | Description |
|---|---|
| Institution + version | e.g. "TUT · 2026 · v1.1.0" |
| Indexed badge | **Indexed** (green) or **Not indexed** (yellow) |
| Qdrant collection | Collection name, shown when indexed |
| Chunk count | Total knowledge chunks in the package |
| Avg / Min / Max confidence | Confidence score statistics across all chunks |
| Entity type breakdown | Count per entity type (programme, module, faculty, etc.) |

---

## Viewing Knowledge Chunks

1. Click **View chunks** on a package card.
2. An inline list of chunks appears below the card.
3. Use the **Filter by type** dropdown to show only one entity type.
4. Use **Previous** / **Next** to page through results.
5. Click any chunk row to expand the full text and source document reference.

---

## Checking Qdrant Index Status

The **Indexed** / **Not indexed** badge on each card shows whether the Qdrant
vector collection for that package exists.

- **Indexed** (green) — the collection exists; Knowledge Search will return results.
- **Not indexed** (yellow) — the collection is missing; Knowledge Search will return
  an error for this institution.

If a package shows "Not indexed", ask a System Admin to trigger a re-index.

---

## Triggering a Re-index (System Admin only)

1. Click **Re-index** to update the existing Qdrant collection with the current
   IKP chunks.
2. Click **Force rebuild** to drop and recreate the collection from scratch.
   Use this when chunk content has changed significantly.

A confirmation message appears when the operation completes, showing the collection
name and the number of chunks indexed.

> **Note:** Re-indexing runs synchronously. For TUT (196 chunks) and UP (28 chunks),
> the operation completes in under 2 seconds. For future larger packages,
> use the CLI instead: `python -m app.knowledge_indexing.index_ikp_chunks --all`

---

## Creating a Knowledge Review Batch

Knowledge Review batches allow QA Officers to review, approve, or reject
extracted IKP knowledge items before they are promoted to the approved IKP.

**When is batch creation available?**  
Only for packages that have a completed ADIP extraction (currently TUT v1.1.0).
The **Create review batch** button is shown only when the package has an
`extracted/` directory.

**Steps:**

1. Click **Create review batch** on the TUT package card.
2. Edit the batch name if desired.
3. Click **Confirm**.
4. The system creates the batch and redirects you to **Knowledge Review** after
   1.8 seconds.

**What happens next?**  
The batch appears in the Knowledge Review Centre (`/knowledge-review`) where
items can be approved, rejected, or edited one by one.

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| "No IKP packages are available" | Non-QA role or wrong institution | Check your role in Settings |
| Badge shows "Not indexed" | Qdrant collection not built | Ask System Admin to re-index |
| "Create review batch" button missing | No ADIP extraction for this package | Run the ADIP pipeline first |
| HTTP 422 on batch creation | Missing institution_id | Ensure your account has an institution assigned |
| Chunks show "—" for source | Source field not in chunk metadata | This is expected for some chunk types |
