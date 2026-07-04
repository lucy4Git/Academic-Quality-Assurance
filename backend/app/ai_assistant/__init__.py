"""AI QA Assistant subsystem.

Provides source-grounded, context-aware responses to academic quality
assurance questions using the Qdrant IKP knowledge base.

In development mode (placeholder embeddings) responses are hash-similarity
ranked rather than semantically ranked.  All responses include an
`is_placeholder_mode` flag so the frontend can surface a dev-mode notice.

Architecture
------------
- assistant_service.py  — intent classification, context retrieval, answer assembly
- prompt_templates.py   — response templates and dev-mode notices
- recommendation_engine.py — rule-based QA improvement recommendations
- routes/ai_assistant.py   — FastAPI route handlers (LecturerRequired min)

Tenant isolation
----------------
- SYSTEM_ADMIN may query any active pilot institution.
- All other roles are locked to their own institution.
- Archived demo institutions (GFU, RCT) are excluded.
- Students cannot access any AI assistant endpoint.
"""
