"""Deterministic, owner-scoped academic credential review."""
from __future__ import annotations
import re
import uuid
from typing import Literal, Protocol
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.parsers.factory import get_parser, is_supported
from app.services.file_service import get_file_content_for_user

router = APIRouter(prefix="/credentials", tags=["Credential review"])

class CredentialVerificationAdapter(Protocol):
    """Optional issuer-registry adapter; implementations must be explicitly configured."""
    name: str
    async def verify(self, claims: dict[str, str | None]) -> tuple[str, str]: ...

class NoCredentialVerificationAdapter:
    name = "none"
    async def verify(self, claims: dict[str, str | None]) -> tuple[str, str]:
        return "not_verified", "No issuer registry or external verification provider is configured."

def get_credential_verifier() -> CredentialVerificationAdapter:
    return NoCredentialVerificationAdapter()

class CredentialField(BaseModel):
    value: str | None
    basis: Literal["document_text", "filename", "none"]
    status: Literal["extracted", "unable_to_determine"]

class CredentialReport(BaseModel):
    file_id: uuid.UUID
    holder_name: CredentialField
    qualification: CredentialField
    institution: CredentialField
    award_date: CredentialField
    credential_number: CredentialField
    authenticity_status: Literal["not_verified", "unable_to_determine"]
    source_status: Literal["owned_upload"]
    originality_status: Literal["unable_to_determine"]
    qualification_status: Literal["extracted", "unable_to_determine"]
    verification_provider: str | None
    verification_note: str
    links_detected: list[str]

_PATTERNS = {
    "holder_name": [r"(?:awarded to|name)\s*[:\-]?\s*([A-Z][A-Za-z .'-]{2,80})"],
    "qualification": [r"((?:Bachelor|Master|Doctor|Diploma|Certificate)[^\n]{0,100})"],
    "institution": [r"((?:University|College|Institute)\s+of\s+[A-Za-z &'-]{2,80}|[A-Za-z &'-]{2,80}\s+(?:University|College|Institute))"],
    "award_date": [r"(?:award(?:ed)?|date)\s*[:\-]?\s*(\d{1,2}[ /-][A-Za-z0-9]{2,12}[ /-]\d{2,4}|\d{4}-\d{2}-\d{2})"],
    "credential_number": [r"(?:credential|certificate|student|serial)\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9-]{4,40})"],
}

def _field(text: str, name: str, filename: str) -> CredentialField:
    for pattern in _PATTERNS[name]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return CredentialField(value=" ".join(match.group(1).split()), basis="document_text", status="extracted")
    if name == "qualification":
        stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        if re.search(r"certificate|diploma|degree", stem, re.IGNORECASE):
            return CredentialField(value=stem, basis="filename", status="extracted")
    return CredentialField(value=None, basis="none", status="unable_to_determine")

@router.post("/{file_id}/review", response_model=CredentialReport)
async def review_credential(file_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CredentialReport:
    db_file, content = await get_file_content_for_user(db, file_id, current_user)
    if db_file.mime_type not in {"application/pdf", "image/png", "image/jpeg"}:
        raise HTTPException(422, "Credential review accepts PDF, PNG, or JPEG files.")
    if not is_supported(db_file.mime_type):
        raise HTTPException(422, "No deterministic parser is available for this file type.")
    extracted = await get_parser(db_file.mime_type).extract(content, db_file.original_filename)
    text = extracted.text or ""
    fields = {name: _field(text, name, db_file.original_filename) for name in _PATTERNS}
    links = list(dict.fromkeys(re.findall(r"https?://[^\s<>\]\)]+", text, re.IGNORECASE)))[:10]
    # URLs/QR payloads are reported only. No network request is made, so an
    # uploaded document cannot turn this endpoint into an SSRF primitive.
    verifier = get_credential_verifier()
    authenticity, adapter_note = await verifier.verify({name: field.value for name, field in fields.items()})
    return CredentialReport(
        file_id=db_file.id, **fields,
        authenticity_status=authenticity if text.strip() else "unable_to_determine",
        source_status="owned_upload", originality_status="unable_to_determine",
        qualification_status=fields["qualification"].status,
        verification_provider=None,
        verification_note=f"Claims were extracted deterministically from the owned upload. {adapter_note} Authenticity and originality are not verified.",
        links_detected=links,
    )