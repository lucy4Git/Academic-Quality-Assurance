"""IKP Management subsystem.

Provides read-only views of Institutional Knowledge Packages (IKPs) stored
in ikp/institutions/{code}/{year}/{version}/, Qdrant indexing status checks,
re-indexing triggers, and Knowledge Review batch creation from IKP content.

Entry points
------------
- ikp_service.py  — pure sync service (reads JSON, queries Qdrant)
- ikp_schemas.py  — Pydantic request/response schemas
- routes/ikp.py   — FastAPI route handlers mounted at /api/v1/ikp
"""
