"""S3-compatible storage backend.

Works with AWS S3, Cloudflare R2, MinIO, Backblaze B2, and any other
S3-compatible object store.

Configuration (from Settings):
    S3_BUCKET           — bucket name (must already exist)
    S3_REGION           — AWS region or provider region (e.g. "auto" for R2)
    S3_ENDPOINT_URL     — custom endpoint for non-AWS providers (R2, MinIO…)
    S3_ACCESS_KEY_ID    — access key / account ID
    S3_SECRET_ACCESS_KEY — secret key

Tenant isolation is enforced at the object-key level: every key is prefixed
with ``{institution_id}/`` so no cross-tenant leakage is possible even if
bucket-level policies are misconfigured.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError

from app.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    """S3-compatible object-storage backend (AWS S3, Cloudflare R2, etc.)."""

    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            region_name=region or "auto",
            endpoint_url=endpoint_url or None,
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
        )

    # ------------------------------------------------------------------
    # StorageBackend interface
    # ------------------------------------------------------------------

    @property
    def backend_name(self) -> str:
        return "s3"

    def build_path(
        self,
        institution_id: uuid.UUID,
        module_id: uuid.UUID,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        suffix = PurePosixPath(filename).suffix.lower()
        return f"{institution_id}/{module_id}/{category}/{file_uuid}{suffix}"

    def build_personal_path(
        self,
        owner_user_id: uuid.UUID,
        workspace_module_id: uuid.UUID | None,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        suffix = PurePosixPath(filename).suffix.lower()
        workspace = str(workspace_module_id) if workspace_module_id else "library"
        return f"users/{owner_user_id}/{workspace}/{category}/{file_uuid}{suffix}"

    async def save(self, data: bytes, relative_path: str) -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=relative_path,
            Body=data,
        )
        return relative_path

    async def read(self, relative_path: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                Bucket=self._bucket,
                Key=relative_path,
            )
            body: bytes = await asyncio.to_thread(response["Body"].read)
            return body
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                raise FileNotFoundError(
                    f"Object not found in S3 bucket: {relative_path!r}"
                ) from exc
            raise

    async def delete(self, relative_path: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=relative_path,
        )

    async def exists(self, relative_path: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.head_object,
                Bucket=self._bucket,
                Key=relative_path,
            )
            return True
        except ClientError:
            return False
