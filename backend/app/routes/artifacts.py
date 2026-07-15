"""D5 — Artifact Engine routes.

Endpoints
---------
POST   /artifacts                        Create artifact
GET    /artifacts                        List user's artifacts (tenant-scoped)
GET    /artifacts/{id}                   Get artifact detail
PATCH  /artifacts/{id}                   Update title/description/content
POST   /artifacts/{id}/version           Save a new version
POST   /artifacts/{id}/archive           Archive
POST   /artifacts/{id}/restore           Restore from archive
DELETE /artifacts/{id}                   Soft-delete (QA+ or owner)
GET    /artifacts/{id}/export            Export as JSON or Markdown
POST   /artifacts/{id}/approve           Approve (QA+)
POST   /artifacts/{id}/assign            Assign to a user
GET    /artifacts/conversation/{conv_id} All artifacts for a conversation
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import LecturerRequired
from app.models.ai_chat import AiArtifact
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.artifact import (
    ArtifactApprovalAction,
    ArtifactAssignRequest,
    ArtifactBrief,
    ArtifactCreate,
    ArtifactExportRequest,
    ArtifactRead,
    ArtifactUpdate,
)

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


def _tenant_filter(user: User):
    """Return institution_id for tenant isolation."""
    if user.role == UserRole.SYSTEM_ADMIN:
        return None
    return user.institution_id


def _check_access(artifact: AiArtifact, user: User) -> None:
    """Raise 403 if user cannot access this artifact."""
    if user.role == UserRole.SYSTEM_ADMIN:
        return
    if artifact.institution_id and artifact.institution_id != user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")


def _check_write(artifact: AiArtifact, user: User) -> None:
    """Raise 403 if user cannot modify this artifact (must be owner or QA+)."""
    _check_access(artifact, user)
    qa_roles = {
        UserRole.SYSTEM_ADMIN,
        UserRole.QUALITY_ASSURANCE_OFFICER,
    }
    if artifact.created_by != user.id and user.role not in qa_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner or a QA Officer may modify this artifact.")


async def _get_artifact(artifact_id: uuid.UUID, db: AsyncSession, user: User) -> AiArtifact:
    art = await db.get(AiArtifact, artifact_id)
    if not art or art.status == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")
    _check_access(art, user)
    return art


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    body: ArtifactCreate,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactRead:
    art = AiArtifact(
        institution_id=user.institution_id,
        tenant_id=user.institution_id,
        created_by=user.id,
        artifact_type=body.artifact_type,
        title=body.title,
        description=body.description,
        content_json=body.content_json,
        rendered_content=body.rendered_content,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        source_context=body.source_context,
        source_evidence=body.source_evidence,
        source_findings=body.source_findings,
        source_frameworks=body.source_frameworks,
        source_assessments=body.source_assessments,
        version_number=1,
        status="saved",
        approval_status="not_required",
        export_formats=["json", "markdown"],
    )
    db.add(art)
    await db.commit()
    await db.refresh(art)
    return ArtifactRead.model_validate(art)


@router.get("", response_model=list[ArtifactBrief])
async def list_artifacts(
    conversation_id: uuid.UUID | None = Query(None),
    artifact_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactBrief]:
    stmt = select(AiArtifact).where(AiArtifact.status != "deleted")

    institution_id = _tenant_filter(user)
    if institution_id:
        stmt = stmt.where(AiArtifact.institution_id == institution_id)
    else:
        # SA — list own artifacts only unless scoped by conversation
        stmt = stmt.where(AiArtifact.created_by == user.id)

    if conversation_id:
        stmt = stmt.where(AiArtifact.conversation_id == conversation_id)
    if artifact_type:
        stmt = stmt.where(AiArtifact.artifact_type == artifact_type)
    if status_filter:
        stmt = stmt.where(AiArtifact.status == status_filter)

    stmt = stmt.order_by(AiArtifact.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    arts = result.scalars().all()
    return [ArtifactBrief.model_validate(a) for a in arts]


@router.get("/conversation/{conversation_id}", response_model=list[ArtifactBrief])
async def list_conversation_artifacts(
    conversation_id: uuid.UUID,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactBrief]:
    stmt = (
        select(AiArtifact)
        .where(
            and_(
                AiArtifact.conversation_id == conversation_id,
                AiArtifact.status != "deleted",
            )
        )
        .order_by(AiArtifact.created_at.asc())
    )
    institution_id = _tenant_filter(user)
    if institution_id:
        stmt = stmt.where(AiArtifact.institution_id == institution_id)
    result = await db.execute(stmt)
    return [ArtifactBrief.model_validate(a) for a in result.scalars().all()]


@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: uuid.UUID,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactRead:
    art = await _get_artifact(artifact_id, db, user)
    return ArtifactRead.model_validate(art)


@router.patch("/{artifact_id}", response_model=ArtifactRead)
async def update_artifact(
    artifact_id: uuid.UUID,
    body: ArtifactUpdate,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactRead:
    art = await _get_artifact(artifact_id, db, user)
    _check_write(art, user)
    if body.title is not None:
        art.title = body.title
    if body.description is not None:
        art.description = body.description
    if body.content_json is not None:
        art.content_json = body.content_json
    if body.rendered_content is not None:
        art.rendered_content = body.rendered_content
    await db.commit()
    await db.refresh(art)
    return ArtifactRead.model_validate(art)


@router.post("/{artifact_id}/version", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
async def save_new_version(
    artifact_id: uuid.UUID,
    body: ArtifactUpdate,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactRead:
    original = await _get_artifact(artifact_id, db, user)
    _check_write(original, user)
    new_art = AiArtifact(
        institution_id=original.institution_id,
        tenant_id=original.tenant_id,
        created_by=user.id,
        artifact_type=original.artifact_type,
        title=body.title or original.title,
        description=body.description or original.description,
        content_json=body.content_json or original.content_json,
        rendered_content=body.rendered_content or original.rendered_content,
        conversation_id=original.conversation_id,
        source_context=original.source_context,
        source_evidence=original.source_evidence,
        source_findings=original.source_findings,
        source_frameworks=original.source_frameworks,
        source_assessments=original.source_assessments,
        version_number=original.version_number + 1,
        parent_artifact_id=original.id,
        status="saved",
        approval_status="not_required",
        export_formats=original.export_formats,
    )
    db.add(new_art)
    await db.commit()
    await db.refresh(new_art)
    return ArtifactRead.model_validate(new_art)


@router.post("/{artifact_id}/archive", response_model=ArtifactBrief)
async def archive_artifact(
    artifact_id: uuid.UUID,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactBrief:
    art = await _get_artifact(artifact_id, db, user)
    _check_write(art, user)
    art.status = "archived"
    art.archived_at = datetime.now(timezone.utc).isoformat()
    await db.commit()
    await db.refresh(art)
    return ArtifactBrief.model_validate(art)


@router.post("/{artifact_id}/restore", response_model=ArtifactBrief)
async def restore_artifact(
    artifact_id: uuid.UUID,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactBrief:
    art = await db.get(AiArtifact, artifact_id)
    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")
    _check_write(art, user)
    art.status = "saved"
    art.archived_at = None
    await db.commit()
    await db.refresh(art)
    return ArtifactBrief.model_validate(art)


@router.delete("/{artifact_id}", status_code=status.HTTP_200_OK)
async def delete_artifact(
    artifact_id: uuid.UUID,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> dict:
    art = await _get_artifact(artifact_id, db, user)
    _check_write(art, user)
    art.status = "deleted"
    await db.commit()
    return {"deleted": True}


@router.get("/{artifact_id}/export")
async def export_artifact(
    artifact_id: uuid.UUID,
    format: str = Query("json", pattern="^(json|markdown)$"),
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> Response:
    art = await _get_artifact(artifact_id, db, user)

    if format == "json":
        payload = {
            "id": str(art.id),
            "artifact_type": art.artifact_type,
            "title": art.title,
            "description": art.description,
            "version_number": art.version_number,
            "status": art.status,
            "content": art.content_json,
            "source_context": art.source_context,
            "source_findings": art.source_findings,
            "source_frameworks": art.source_frameworks,
            "created_at": art.created_at.isoformat() if art.created_at else None,
        }
        return Response(
            content=json.dumps(payload, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="artifact_{art.id}.json"'},
        )

    # markdown
    md_lines = [
        f"# {art.title}",
        f"\n**Type:** {art.artifact_type}  ",
        f"**Version:** {art.version_number}  ",
        f"**Status:** {art.status}  ",
        f"**Created:** {art.created_at}  ",
        "",
    ]
    if art.description:
        md_lines += [f"> {art.description}", ""]
    if art.rendered_content:
        md_lines.append(art.rendered_content)
    elif art.content_json:
        md_lines.append("```json")
        md_lines.append(json.dumps(art.content_json, indent=2, default=str))
        md_lines.append("```")

    art.last_exported_at = datetime.now(timezone.utc).isoformat()
    art.last_exported_format = format
    await db.commit()

    return PlainTextResponse(
        content="\n".join(md_lines),
        headers={"Content-Disposition": f'attachment; filename="artifact_{art.id}.md"'},
    )


@router.post("/{artifact_id}/approve", response_model=ArtifactBrief)
async def approve_or_reject_artifact(
    artifact_id: uuid.UUID,
    body: ArtifactApprovalAction,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactBrief:
    if user.role not in {UserRole.SYSTEM_ADMIN, UserRole.QUALITY_ASSURANCE_OFFICER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only QA Officers may approve/reject artifacts.")
    art = await _get_artifact(artifact_id, db, user)
    art.approval_status = "approved" if body.action == "approve" else "rejected"
    art.approved_by = user.id
    await db.commit()
    await db.refresh(art)
    return ArtifactBrief.model_validate(art)


@router.post("/{artifact_id}/assign", response_model=ArtifactBrief)
async def assign_artifact(
    artifact_id: uuid.UUID,
    body: ArtifactAssignRequest,
    user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ArtifactBrief:
    art = await _get_artifact(artifact_id, db, user)
    _check_write(art, user)
    art.assigned_to = body.assigned_to
    await db.commit()
    await db.refresh(art)
    return ArtifactBrief.model_validate(art)
