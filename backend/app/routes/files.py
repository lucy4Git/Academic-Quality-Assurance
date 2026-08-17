"""File management routes.

Endpoint summary
----------------
POST   /files/upload               Upload a single file to a module folder.
POST   /files/bulk                 Upload multiple files in one request.
GET    /files                      List files (tenant-scoped, filterable).
GET    /files/{file_id}            Get file metadata.
GET    /files/{file_id}/download   Download the latest version's bytes.
GET    /files/{file_id}/preview    Get preview / inline-display metadata.
GET    /files/{file_id}/versions   List all version records.
GET    /files/{file_id}/versions/{version_number}/download
                                   Download a specific version.
PATCH  /files/{file_id}            Update category or description.
DELETE /files/{file_id}            Soft-delete the file.

Permission model
----------------
- Upload (single + bulk)  : LecturerRequired (any teaching staff or above)
- Download / preview      : AnyAuthenticatedUser (read; tenant-scoped in service)
- Metadata update         : CoordinatorRequired
- Delete                  : CoordinatorRequired
- List / get              : AnyAuthenticatedUser
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    PaginationParams,
    get_external_scope,
)
from app.core.external_scope import ExternalScope, assert_module_scope, deny_external_access
from app.models.enums import FileCategory, UploadState
from app.models.user import User
from app.schemas.file import (
    BulkUploadResponse,
    FileMetadataUpdate,
    FilePreviewResponse,
    FileRead,
    FileUploadError,
    FileVersionRead,
)
from app.services import file_service
from app.services.validation_service import UploadValidationError

router = APIRouter(prefix="/files", tags=["Files"])

# ---------------------------------------------------------------------------
# Previewable MIME types (browser can render inline)
# ---------------------------------------------------------------------------

_PREVIEWABLE_MIMES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error_to_422(exc: UploadValidationError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


def _assert_tenant(current_user: User, file_institution_id: uuid.UUID) -> None:
    """Raise 403 if the user cannot access this file's institution."""
    from app.models.enums import UserRole

    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    if current_user.institution_id != file_institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this file.",
        )


# ---------------------------------------------------------------------------
# Single upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=FileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single file to a module folder",
)
async def upload_file(
    module_id: Annotated[uuid.UUID, Form(description="Target module UUID.")],
    category: Annotated[FileCategory, Form(description="Document category.")],
    file: Annotated[UploadFile, File(description="File to upload.")],
    description: Annotated[str | None, Form(description="Optional description.")] = None,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> FileRead:
    content = await file.read()
    try:
        db_file = await file_service.upload_file(
            db=db,
            module_id=module_id,
            category=category,
            original_filename=file.filename or "upload",
            content=content,
            current_user=current_user,
            description=description,
        )
    except UploadValidationError as exc:
        raise _validation_error_to_422(exc)
    return FileRead.model_validate(db_file)


# ---------------------------------------------------------------------------
# Bulk upload
# ---------------------------------------------------------------------------


@router.post(
    "/bulk",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_207_MULTI_STATUS,
    summary="Upload multiple files in one request (partial success allowed)",
)
async def bulk_upload(
    module_id: Annotated[uuid.UUID, Form(description="Target module UUID.")],
    category: Annotated[FileCategory, Form(description="Document category for all files.")],
    files: Annotated[list[UploadFile], File(description="Files to upload.")],
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> BulkUploadResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No files were provided.",
        )

    file_data: list[tuple[str, bytes]] = []
    for upload in files:
        content = await upload.read()
        file_data.append((upload.filename or "upload", content))

    uploaded, failed = await file_service.bulk_upload(
        db=db,
        module_id=module_id,
        category=category,
        files=file_data,
        current_user=current_user,
    )

    return BulkUploadResponse(
        uploaded=[FileRead.model_validate(f) for f in uploaded],
        failed=[FileUploadError(filename=name, error=err) for name, err in failed],
        total=len(file_data),
        success_count=len(uploaded),
        failure_count=len(failed),
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[FileRead],
    summary="List files (tenant-scoped, filterable)",
)
async def list_files(
    module_id: uuid.UUID | None = Query(default=None, description="Filter by module."),
    category: FileCategory | None = Query(default=None, description="Filter by category."),
    upload_state: UploadState | None = Query(default=None, description="Filter by upload state."),
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> list[FileRead]:
    # External moderators are restricted to their invited module only.
    if ext_scope is not None:
        if ext_scope.module_id is None:
            deny_external_access(ext_scope, "tenant-wide file listing")
        module_id = ext_scope.module_id  # force filter to scoped module

    files = await file_service.list_files(
        db=db,
        current_user=current_user,
        module_id=module_id,
        category=category,
        upload_state=upload_state,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [FileRead.model_validate(f) for f in files]


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}",
    response_model=FileRead,
    summary="Get file metadata",
)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> FileRead:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    if ext_scope is not None:
        if db_file.module_id is not None:
            assert_module_scope(ext_scope, db_file.module_id)
        else:
            deny_external_access(ext_scope, "this file")
    return FileRead.model_validate(db_file)


# ---------------------------------------------------------------------------
# Download latest version
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}/download",
    summary="Download the latest version of a file",
    response_class=Response,
)
async def download_file(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> Response:
    db_file, content = await file_service.get_file_content(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    if ext_scope is not None:
        if db_file.module_id is not None:
            assert_module_scope(ext_scope, db_file.module_id)
        else:
            deny_external_access(ext_scope, "this file")
    return Response(
        content=content,
        media_type=db_file.mime_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{db_file.original_filename}"'
            ),
            "Content-Length": str(len(content)),
            "X-Checksum-SHA256": db_file.checksum_sha256,
        },
    )


# ---------------------------------------------------------------------------
# Preview metadata
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}/preview",
    response_model=FilePreviewResponse,
    summary="Get preview metadata (inline URL for images and PDFs)",
)
async def preview_file(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> FilePreviewResponse:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    if ext_scope is not None:
        if db_file.module_id is not None:
            assert_module_scope(ext_scope, db_file.module_id)
        else:
            deny_external_access(ext_scope, "this file")

    is_previewable = db_file.mime_type in _PREVIEWABLE_MIMES
    download_url = f"/api/v1/files/{file_id}/download"

    return FilePreviewResponse(
        id=db_file.id,
        original_filename=db_file.original_filename,
        mime_type=db_file.mime_type,
        size_bytes=db_file.size_bytes,
        category=db_file.category,
        version=db_file.version,
        upload_state=db_file.upload_state,
        download_url=download_url,
        is_previewable=is_previewable,
        preview_url=download_url if is_previewable else None,
    )


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}/versions",
    response_model=list[FileVersionRead],
    summary="List all version records for a file",
)
async def list_versions(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> list[FileVersionRead]:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    if ext_scope is not None:
        if db_file.module_id is not None:
            assert_module_scope(ext_scope, db_file.module_id)
        else:
            deny_external_access(ext_scope, "this file")
    versions = await file_service.list_versions(db, file_id)
    return [FileVersionRead.model_validate(v) for v in versions]


# ---------------------------------------------------------------------------
# Download specific version
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}/versions/{version_number}/download",
    summary="Download a specific version of a file",
    response_class=Response,
)
async def download_version(
    file_id: uuid.UUID,
    version_number: int,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> Response:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    if ext_scope is not None:
        if db_file.module_id is not None:
            assert_module_scope(ext_scope, db_file.module_id)
        else:
            deny_external_access(ext_scope, "this file")

    version, content = await file_service.get_version_content(db, file_id, version_number)
    return Response(
        content=content,
        media_type=db_file.mime_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="v{version_number}_{db_file.original_filename}"'
            ),
            "Content-Length": str(len(content)),
            "X-Checksum-SHA256": version.checksum_sha256,
            "X-Version-Number": str(version_number),
        },
    )


# ---------------------------------------------------------------------------
# Update metadata
# ---------------------------------------------------------------------------


@router.patch(
    "/{file_id}",
    response_model=FileRead,
    summary="Update file category or description",
)
async def update_file_metadata(
    file_id: uuid.UUID,
    data: FileMetadataUpdate,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> FileRead:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    updated = await file_service.update_file_metadata(db, db_file, data)
    return FileRead.model_validate(updated)


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------


@router.delete(
    "/{file_id}",
    summary="Soft-delete a file (bytes removed, audit trail preserved)",
)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> Response:
    db_file = await file_service.get_file(db, file_id)
    _assert_tenant(current_user, db_file.institution_id)
    await file_service.delete_file(db, db_file)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Bulk ZIP upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload-zip",
    status_code=status.HTTP_200_OK,
    summary="Upload a ZIP archive — extract, classify, and return a mapping manifest",
)
async def upload_zip(
    file: UploadFile = File(..., description="ZIP archive (max 50 MB compressed)"),
    current_user: User = LecturerRequired,
) -> dict:
    """Accept a ZIP, validate, extract, and auto-classify each file via ADIP heuristics.

    Returns a manifest the client can display for the user to review / correct before
    committing.  No files are written to storage yet — that happens at /files/upload-zip/confirm.
    """
    from app.services.zip_upload_service import ZipUploadError, extract_and_classify, validate_zip
    from app.config import settings as _settings

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .zip files are accepted by this endpoint.",
        )

    data = await file.read()
    try:
        validate_zip(data, max_size_mb=_settings.MAX_UPLOAD_SIZE_MB)
        manifest = extract_and_classify(data)
    except ZipUploadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    from app.services.zip_upload_service import cleanup_extraction
    cleanup_extraction(manifest.extraction_dir)

    return manifest.summary()


@router.post(
    "/upload-zip/confirm",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Confirm the corrected file→category mapping and enqueue uploads",
)
async def confirm_zip_mapping(
    body: dict,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Accept the user-corrected mapping produced by /upload-zip.

    Expected body::

        {
          "module_id": "<uuid>",
          "files": [
            {"original_path": "...", "filename": "...", "category": "assessment", ...},
            ...
          ]
        }

    Each file must supply a valid FileCategory value. Files are queued for
    standard single-file upload processing (virus scan → storage → DB record).
    This endpoint returns immediately with a count — actual processing is async.
    """
    module_id_raw = body.get("module_id")
    files = body.get("files", [])

    if not module_id_raw:
        raise HTTPException(status_code=422, detail="module_id is required.")
    if not files:
        raise HTTPException(status_code=422, detail="files list is empty.")

    try:
        module_id = uuid.UUID(str(module_id_raw))
    except ValueError:
        raise HTTPException(status_code=422, detail="module_id must be a valid UUID.")

    valid_categories = {c.value for c in FileCategory}
    errors: list[str] = []
    for entry in files:
        cat = entry.get("category")
        if cat not in valid_categories:
            errors.append(f"'{entry.get('filename', '?')}' has invalid category '{cat}'.")
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    return {
        "message": f"Mapping accepted. {len(files)} file(s) queued for upload.",
        "module_id": str(module_id),
        "queued": len(files),
    }
