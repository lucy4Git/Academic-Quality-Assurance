# ADIP — Knowledge Indexing Engine (Layer 8)

**Document ID:** ADIP-L8-001  
**Version:** 1.0.0  
**Status:** Architecture Design  
**Last Updated:** 2026-06-29

---

## 1. Purpose

The Knowledge Indexing Engine persists validated, mapped knowledge into four complementary indexes that serve different retrieval needs:

1. **Structured database records** — typed, queryable IKP entities (PostgreSQL)
2. **Full-text index** — keyword search over document content (PostgreSQL FTS or Elasticsearch)
3. **Vector index** — semantic similarity search (Qdrant — already in AQAA)
4. **Knowledge graph** — entity relationships for graph traversal by AI agents

Each index serves a different consumer: structured records serve deterministic lookups; full-text serves compliance keyword searches; vector serves AI reasoning; knowledge graph serves graph traversal.

---

## 2. Index 1 — Structured Database Records (PostgreSQL)

**Purpose:** Typed, queryable IKP entity records that AQAA's application code uses directly.

**Tables produced by ADIP indexing:**
- `adip_document_records` — one row per registered document
- `adip_extraction_chunks` — all extracted text chunks
- `adip_document_tables` — all extracted tables
- `adip_knowledge_candidates` — proposed IKP field mappings (with confidence and status)
- `adip_provenance_anchors` — fine-grained provenance records
- `adip_contradictions` — detected value conflicts

**IKP entity tables updated by ADIP (via seed script, not direct write):**
- `institutions`, `faculties`, `departments`, `programmes`, `modules`
- Updated via `seed-from-ikp.py` which reads ADIP output

**Key query patterns:**
```sql
-- Find all approved candidates for a specific programme field
SELECT value, confidence, provenance_anchor_id
FROM adip_knowledge_candidates
WHERE institution_id = $1
  AND ikp_entity_type = 'programme'
  AND ikp_entity_key = 'Diploma in Computer Science'
  AND ikp_field_name = 'nqf_level'
  AND status = 'auto_approved'
ORDER BY confidence DESC;

-- Find all documents for an institution not yet fully indexed
SELECT * FROM adip_document_records
WHERE institution_id = $1
  AND processing_state != 'ready'
ORDER BY registered_at DESC;
```

---

## 3. Index 2 — Full-Text Index

**Purpose:** Keyword search over all extracted document content for compliance officers and AI agents.

**Implementation options (choose one):**
| Option | Complexity | Performance | When to Use |
|--------|-----------|-------------|-------------|
| PostgreSQL FTS (`tsvector`) | Low | Medium | Pilot phase — already in stack |
| Elasticsearch | High | High | Production (Phase 8) |
| Typesense | Medium | High | Future evaluation |

**Pilot implementation (PostgreSQL FTS):**

```sql
-- Conceptual schema
CREATE TABLE adip_full_text_index (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    institution_id UUID NOT NULL,
    chunk_id UUID,
    page_number INTEGER,
    content TEXT,
    content_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    document_type TEXT,
    academic_year TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON adip_full_text_index USING GIN(content_vector);
```

**Example compliance keyword search:**
```sql
SELECT document_id, page_number, content, ts_rank(content_vector, query) AS rank
FROM adip_full_text_index, to_tsquery('english', 'NQF & level & 6') query
WHERE institution_id = $1
  AND content_vector @@ query
ORDER BY rank DESC
LIMIT 20;
```

---

## 4. Index 3 — Vector Index (Qdrant)

**Purpose:** Semantic similarity search — finding relevant document content by meaning, not keyword. Powers AI audit agent RAG (Retrieval-Augmented Generation).

**Qdrant collection design:**

```
Collection: adip_chunks_{institution_code}
  (separate collection per institution for tenant isolation)
  
Vector dimensions: 768 (sentence-transformers/all-mpnet-base-v2)
Distance metric: Cosine

Payload schema per vector:
{
  "chunk_id": "UUID",
  "document_id": "UUID",
  "document_type": "PROSPECTUS_FACULTY",
  "page_number": 12,
  "text": "Diploma in Computer Science (NQF level 6)",
  "section_path": ["Programmes Offered", "Computer Science"],
  "academic_year": "2026",
  "confidence": 0.96,
  "ikp_entity_type": "programme",
  "ikp_entity_key": "Diploma in Computer Science"
}
```

**Chunking strategy for vectors:**
- Chunk size: 400 tokens (approximately 300 words)
- Overlap: 50 tokens between consecutive chunks
- Chunk boundaries: prefer sentence/paragraph boundaries
- Each chunk produces one vector embedding

**Embedding model:**
| Model | Dimensions | Speed | Accuracy | Suitable For |
|-------|-----------|-------|---------|-------------|
| `sentence-transformers/all-mpnet-base-v2` | 768 | Medium | High | Pilot (local) |
| `text-embedding-3-small` (OpenAI) | 1536 | Fast | High | Production |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | Medium | High | Multilingual support |

**For pilot:** Use `all-mpnet-base-v2` locally. No external API dependency for embedding.

**Vector query example (AI agent retrieval):**
```python
# Conceptual — not production code
results = qdrant_client.search(
    collection_name=f"adip_chunks_tut",
    query_vector=embed("What are the admission requirements for Computer Science?"),
    query_filter={"must": [{"key": "document_type", "match": {"value": "PROSPECTUS_FACULTY"}}]},
    limit=5
)
# Returns: top 5 semantically similar chunks with payloads
```

---

## 5. Index 4 — Knowledge Graph

**Purpose:** Graph-traversal queries — finding chains of relationships between entities.

**Implementation (pilot):** PostgreSQL adjacency table (simple, no additional infrastructure)

**Future implementation (production):** Neo4j or Amazon Neptune (Phase 8)

**Node types:**
```
Institution → Campus
Institution → Faculty → Department → Programme → Module
Programme → AdmissionRequirement
Module → LearningOutcome → Assessment
Programme → QAPolicy
```

**Edge types:**
```
LOCATED_AT, HAS_FACULTY, HAS_DEPARTMENT, OFFERS_PROGRAMME, 
CONTAINS_MODULE, HAS_OUTCOME, ASSESSED_BY, GOVERNED_BY, 
REQUIRES_EVIDENCE, POPULATED_FROM (document → entity)
```

**PostgreSQL adjacency table (pilot):**
```sql
CREATE TABLE adip_knowledge_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID NOT NULL,
    source_type TEXT,       -- 'institution', 'faculty', 'programme', etc.
    source_id UUID,
    edge_type TEXT,         -- 'HAS_FACULTY', 'CONTAINS_MODULE', etc.
    target_type TEXT,
    target_id UUID,
    confidence FLOAT,
    provenance_anchor_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Graph traversal for AI audit agent:**
```
Query: "What evidence is required for Diploma in Computer Science?"
→ Find Programme node (Diploma in Computer Science)
→ Traverse GOVERNED_BY → QAPolicy (assessment policy)
→ Traverse HAS_OUTCOME → LearningOutcome nodes
→ Traverse ASSESSED_BY → Assessment nodes
→ Retrieve REQUIRES_EVIDENCE edges
→ Return: structured evidence requirements per assessment
```

---

## 6. Index Synchronisation

When a new document version is ingested (e.g., 2027 TUT ICT Prospectus):
1. New extraction runs → new chunks, tables, candidates
2. New vectors added to Qdrant (not replacing old — tag by `academic_year`)
3. Old knowledge graph nodes marked `superseded`
4. New nodes added with `academic_year = 2027`
5. Historical queries can specify `academic_year` to retrieve past state

**ADIP indexes support point-in-time queries** — critical for answering: "What did AQAA know about this programme in 2025?"
