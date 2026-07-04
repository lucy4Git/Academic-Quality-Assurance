"""Institutional Knowledge Package (IKP) vector indexing subsystem.

Loads AI-ready knowledge chunks from IKP JSON files into Qdrant for semantic
search.  Strict tenant isolation is enforced: one Qdrant collection per
institution/version, and every vector payload carries institution metadata.

Entry points
------------
CLI:    python -m app.knowledge_indexing.index_ikp_chunks --help
API:    POST /api/v1/knowledge-index/index
        GET  /api/v1/knowledge-index/status
        POST /api/v1/knowledge-search
"""
