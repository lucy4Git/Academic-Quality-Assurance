"""File upload and metadata schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FileCategory, UploadState


class FileVersionRead(BaseModel):
    """One entry in a file's version history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: int
    original_filename: str
    size_bytes: int
    checksum_sha256: str
    created_by_id: uuid.UUID | None
    created_at: datetime


class FileRead(BaseModel):
    """Full metadata for an uploaded file (never includes binary content)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID | None
    module_id: uuid.UUID | None
    owner_user_id: uuid.UUID | None
    workspace_module_id: uuid.UUID | None
    original_filename: str
    mime_type: str
    extension: str
    size_bytes: int
    category: FileCategory
    version: int
    checksum_sha256: str
    upload_state: UploadState
    uploaded_by_id: uuid.UUID | None
    description: str | None
    is_library_item: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class FileMetadataUpdate(BaseModel):
    """Fields a coordinator may update on an existing file record."""

    category: FileCategory | None = None
    description: str | None = Field(default=None, max_length=1000)
    is_library_item: bool | None = None


class FileUploadError(BaseModel):
    """Per-file error entry returned in a bulk upload response."""

    filename: str
    error: str


class BulkUploadResponse(BaseModel):
    """Summary returned by ``POST /files/bulk``."""

    uploaded: list[FileRead]
    failed: list[FileUploadError]
    total: int
    success_count: int
    failure_count: int


class FilePreviewResponse(BaseModel):
    """Returned by ``GET /files/{id}/preview``."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    category: FileCategory
    version: int
    upload_state: UploadState
    download_url: str          # e.g.  /api/v1/files/{id}/download
    is_previewable: bool       # True for images and PDFs
    preview_url: str | None    # direct URL for inline preview (images / PDFs)
