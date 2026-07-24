"""File upload, versioning, retrieval, and deletion service.

Orchestration flow for a single upload
---------------------------------------
1. Resolve the target module via JOIN to get institution_id (validates module exists).
2. Validate file content: extension → size → magic bytes → ZIP safety.
3. Compute SHA-256 checksum.
4. Run the virus-scan hook → READY or QUARANTINED.
5. Check for an existing non-deleted file with (module_id, category, original_filename):
   - Match found  → bump version, update File record, create new FileVersion.
   - No match     → create File (v1) and FileVersion (v1).
6. Build storage path, persist bytes via the storage backend.
7. Commit and return the File ORM object.
"""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import FileCategory, UploadState
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.schemas.file import FileMetadataUpdate
from app.services.scan_service import scan_file
from app.services.validation_service import validate_upload
from app.storage.factory import get_storage


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _resolve_module_institution(
    db: AsyncSession, module_id: uuid.UUID
) -> uuid.UUID:
    """Return institution_id for *module_id* via the hierarchy JOIN.

    Raises NotFoundError if the module does not exist.
    """
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.module import Module
    from app.models.programme import Programme

    result = await db.execute(
        select(Faculty.institution_id)
        .join(Department, Faculty.id == Department.faculty_id)
        .join(Programme, Department.id == Programme.department_id)
        .join(Module, Programme.id == Module.programme_id)
        .where(Module.id == module_id)
    )
    institution_id = result.scalar_one_or_none()
    if institution_id is None:
        raise NotFoundError("Module", module_id)
    return institution_id


async def _find_existing_file(
    db: AsyncSession,
    module_id: uuid.UUID,
    category: FileCategory,
    original_filename: str,
) -> File | None:
    result = await db.execute(
        select(File).where(
            File.module_id == module_id,
            File.category == category,
            File.original_filename == original_filename,
            File.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


async def upload_file(
    db: AsyncSession,
    module_id: uuid.UUID,
    category: FileCategory,
    original_filename: str,
    content: bytes,
    current_user: User,
    description: str | None = None,
) -> File:
    """Validate, scan, store, and persist *content* as a new file or new version.

    Raises:
        NotFoundError: module does not exist.
        UploadValidationError: file content fails a validation check.
        ConflictError: an existing version of this file is currently quarantined.
    """
    institution_id = await _resolve_module_institution(db, module_id)

    # Tenant isolation: non-admin users may only upload to their own institution's modules
    from app.models.enums import UserRole as _Role
    from app.core.exceptions import NotFoundError as _NF
    if current_user.role != _Role.SYSTEM_ADMIN:
        if current_user.institution_id != institution_id:
            # Return 404 (not 403) to avoid leaking cross-tenant module existence
            raise _NF("Module", module_id)

    ext, mime_type = validate_upload(original_filename, content)
    checksum = _sha256(content)

    scan_result = await scan_file(content)
    final_state = UploadState.READY if scan_result.is_clean else UploadState.QUARANTINED

    existing_file = await _find_existing_file(db, module_id, category, original_filename)

    if existing_file is not None and existing_file.upload_state == UploadState.QUARANTINED:
        raise ConflictError(
            f"'{original_filename}' is currently quarantined. "
            "Contact your administrator before re-uploading."
        )

    storage = get_storage()
    file_uuid = existing_file.id if existing_file is not None else uuid.uuid4()
    new_version = (existing_file.version + 1) if existing_file is not None else 1

    stored_path = storage.build_path(
        institution_id=institution_id,
        module_id=module_id,
        category=category.value,
        file_uuid=file_uuid,
        filename=f"v{new_version}_{original_filename}",
    )
    await storage.save(content, stored_path)

    if existing_file is None:
        db_file = File(
            id=file_uuid,
            institution_id=institution_id,
            module_id=module_id,
            original_filename=original_filename,
            stored_path=stored_path,
            mime_type=mime_type,
            extension=ext,
            size_bytes=len(content),
            category=category,
            version=1,
            checksum_sha256=checksum,
            upload_state=final_state,
            uploaded_by_id=current_user.id,
            description=description,
        )
        db.add(db_file)
    else:
        existing_file.stored_path = stored_path
        existing_file.mime_type = mime_type
        existing_file.extension = ext
        existing_file.size_bytes = len(content)
        existing_file.version = new_version
        existing_file.checksum_sha256 = checksum
        existing_file.upload_state = final_state
        existing_file.uploaded_by_id = current_user.id
        if description is not None:
            existing_file.description = description
        db_file = existing_file

    db_version = FileVersion(
        file_id=file_uuid,
        version_number=new_version,
        original_filename=original_filename,
        stored_path=stored_path,
        size_bytes=len(content),
        checksum_sha256=checksum,
        created_by_id=current_user.id,
    )
    db.add(db_version)

    try:
        await db.commit()
    except Exception:
        # DB commit failed — remove the already-written object so storage and
        # database remain consistent (no orphaned S3/local objects).
        try:
            await storage.delete(stored_path)
        except Exception:
            pass  # best-effort; the object may not have been written
        raise

    await db.refresh(db_file)
    return db_file


# ---------------------------------------------------------------------------
# Bulk upload
# ---------------------------------------------------------------------------


async def bulk_upload(
    db: AsyncSession,
    module_id: uuid.UUID,
    category: FileCategory,
    files: list[tuple[str, bytes]],
    current_user: User,
) -> tuple[list[File], list[tuple[str, str]]]:
    """Upload multiple files independently; partial success is allowed.

    Returns:
        (uploaded_files, [(filename, error_message), ...])
    """
    uploaded: list[File] = []
    failed: list[tuple[str, str]] = []

    for filename, content in files:
        try:
            db_file = await upload_file(
                db=db,
                module_id=module_id,
                category=category,
                original_filename=filename,
                content=content,
                current_user=current_user,
            )
            uploaded.append(db_file)
        except Exception as exc:
            await db.rollback()
            failed.append((filename, str(exc)))

    return uploaded, failed


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


async def get_file(db: AsyncSession, file_id: uuid.UUID) -> File:
    """Return a non-deleted File or raise ``NotFoundError``."""
    result = await db.execute(
        select(File).where(File.id == file_id, File.is_deleted.is_(False))
    )
    db_file = result.scalar_one_or_none()
    if db_file is None:
        raise NotFoundError("File", file_id)
    return db_file


async def list_files(
    db: AsyncSession,
    current_user: User,
    module_id: uuid.UUID | None = None,
    category: FileCategory | None = None,
    upload_state: UploadState | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[File]:
    """Return non-deleted files scoped to the current user's institution."""
    from app.models.enums import UserRole

    query = (
        select(File)
        .where(File.is_deleted.is_(False))
        .order_by(File.created_at.desc())
    )

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id is None:
            return []
        query = query.where(File.institution_id == current_user.institution_id)

    if module_id is not None:
        query = query.where(File.module_id == module_id)
    if category is not None:
        query = query.where(File.category == category)
    if upload_state is not None:
        query = query.where(File.upload_state == upload_state)

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_file_content(db: AsyncSession, file_id: uuid.UUID) -> tuple[File, bytes]:
    """Return (File, raw_bytes) from storage.

    Raises:
        NotFoundError: file record missing or storage path not found.
        DomainPermissionError: file is quarantined.
    """
    from app.core.exceptions import PermissionError as DomainPermissionError

    db_file = await get_file(db, file_id)

    if db_file.upload_state == UploadState.QUARANTINED:
        raise DomainPermissionError(
            "This file has been quarantined and cannot be downloaded. "
            "Contact your system administrator."
        )

    storage = get_storage()
    try:
        content = await storage.read(db_file.stored_path)
    except FileNotFoundError:
        raise NotFoundError("File content", file_id)

    return db_file, content


async def list_versions(db: AsyncSession, file_id: uuid.UUID) -> list[FileVersion]:
    """Return all versions ordered by version_number ascending."""
    await get_file(db, file_id)
    result = await db.execute(
        select(FileVersion)
        .where(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number)
    )
    return list(result.scalars().all())


async def get_version_content(
    db: AsyncSession, file_id: uuid.UUID, version_number: int
) -> tuple[FileVersion, bytes]:
    """Return a specific version record and its raw bytes."""
    await get_file(db, file_id)
    result = await db.execute(
        select(FileVersion).where(
            FileVersion.file_id == file_id,
            FileVersion.version_number == version_number,
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise NotFoundError(f"File version {version_number}", file_id)

    storage = get_storage()
    try:
        content = await storage.read(version.stored_path)
    except FileNotFoundError:
        raise NotFoundError(f"File version {version_number} content", file_id)

    return version, content


# ---------------------------------------------------------------------------
# Metadata update
# ---------------------------------------------------------------------------


async def update_file_metadata(
    db: AsyncSession,
    db_file: File,
    data: FileMetadataUpdate,
) -> File:
    """Apply PATCH-style metadata changes (category, description)."""
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(db_file, field, value)
    await db.commit()
    await db.refresh(db_file)
    return db_file


# ---------------------------------------------------------------------------
# Deletion (soft)
# ---------------------------------------------------------------------------


async def delete_file(db: AsyncSession, db_file: File) -> None:
    """Soft-delete: mark is_deleted=True and remove bytes from storage.

    FileVersion rows are retained for audit trail purposes.
    """
    storage = get_storage()
    await storage.delete(db_file.stored_path)
    db_file.is_deleted = True
    await db.commit()


# ---------------------------------------------------------------------------
# Module folder summary (used by audit agents)
# ---------------------------------------------------------------------------


async def get_module_folder_summary(
    db: AsyncSession, module_id: uuid.UUID
) -> dict[str, list[File]]:
    """Return READY, non-deleted files for *module_id* grouped by category."""
    result = await db.execute(
        select(File).where(
            File.module_id == module_id,
            File.is_deleted.is_(False),
            File.upload_state == UploadState.READY,
        )
    )
    grouped: dict[str, list[File]] = {}
    for f in result.scalars().all():
        grouped.setdefault(f.category.value, []).append(f)
    return grouped
