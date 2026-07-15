"""D1 — Unified Context Engine.

Resolves every request to a fully-typed context object covering user, role,
tenant, institution, faculty, department, programme, module, academic period,
applicable frameworks, and available findings/audits.

Precedence order (first match wins):
  1. Explicit entity reference in the prompt
  2. Workspace context passed by the client
  3. Conversation context from session history
  4. Role-scope (user's assigned institution/dept/programme/module)
  5. Single unambiguous available entity for that scope
  6. Clarification required

The context object is INTERNAL — it is never serialised and returned to the
client directly.  Only the public fields (institution_name, etc.) travel over
the wire inside SSE events.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.department import Department
from app.models.enums import FindingStatus, UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.quality_framework import QualityFramework
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


@dataclass
class ResolvedContext:
    """Fully resolved request context — internal use only."""

    # ── Identity ────────────────────────────────────────────────────────────
    user_id: uuid.UUID | None = None
    user_name: str = ""
    role: UserRole | None = None

    # ── Tenant / Institution ─────────────────────────────────────────────
    institution_id: uuid.UUID | None = None
    institution_name: str = ""
    institution_code: str = ""

    # ── Hierarchy ───────────────────────────────────────────────────────────
    faculty_id: uuid.UUID | None = None
    faculty_name: str = ""

    department_id: uuid.UUID | None = None
    department_name: str = ""

    programme_id: uuid.UUID | None = None
    programme_name: str = ""
    programme_code: str = ""

    module_id: uuid.UUID | None = None
    module_name: str = ""
    module_code: str = ""

    # ── Academic period ──────────────────────────────────────────────────
    academic_year: str = ""
    semester: str = ""

    # ── Frameworks ──────────────────────────────────────────────────────────
    applicable_framework_ids: list[uuid.UUID] = field(default_factory=list)
    applicable_framework_codes: list[str] = field(default_factory=list)

    # ── Active findings ──────────────────────────────────────────────────
    open_finding_ids: list[uuid.UUID] = field(default_factory=list)
    open_finding_count: int = 0

    # ── Resolution metadata ──────────────────────────────────────────────
    confidence: float = 1.0
    resolution_source: str = "explicit"  # explicit | workspace | conversation | scope | single | clarification
    missing_context: list[str] = field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str = ""
    permission_denied: bool = False
    permission_reason: str = ""

    def to_indicator(self) -> dict[str, str]:
        """Return a compact dict for the frontend context indicator."""
        parts: dict[str, str] = {}
        if self.institution_code:
            parts["institution"] = self.institution_name or self.institution_code
        if self.faculty_name:
            parts["faculty"] = self.faculty_name
        if self.programme_name:
            parts["programme"] = self.programme_name
        if self.module_code:
            parts["module"] = f"{self.module_code} – {self.module_name}" if self.module_name else self.module_code
        if self.academic_year:
            period = self.academic_year
            if self.semester:
                period += f" Sem {self.semester}"
            parts["period"] = period
        return parts

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "institution_code": self.institution_code,
            "institution_name": self.institution_name,
            "faculty_name": self.faculty_name,
            "department_name": self.department_name,
            "programme_name": self.programme_name,
            "programme_code": self.programme_code,
            "module_name": self.module_name,
            "module_code": self.module_code,
            "module_id": str(self.module_id) if self.module_id else None,
            "programme_id": str(self.programme_id) if self.programme_id else None,
            "academic_year": self.academic_year,
            "semester": self.semester,
            "applicable_framework_codes": self.applicable_framework_codes,
            "open_finding_count": self.open_finding_count,
            "confidence": self.confidence,
            "resolution_source": self.resolution_source,
            "requires_clarification": self.requires_clarification,
            "clarification_question": self.clarification_question,
            "indicator": self.to_indicator(),
        }


# ---------------------------------------------------------------------------
# Entity mention extraction from natural language
# ---------------------------------------------------------------------------

_MODULE_CODE_RE = re.compile(
    r"\b([A-Z]{2,6}\s*\d{3,4}[A-Z]?)\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_SEMESTER_RE = re.compile(r"\bsem(ester)?\s*([12])\b", re.IGNORECASE)


def _extract_mentions(prompt: str) -> dict[str, Any]:
    """Extract entity mentions (codes, years, semesters) from a prompt."""
    mentions: dict[str, Any] = {}

    codes = _MODULE_CODE_RE.findall(prompt.upper())
    if codes:
        mentions["module_codes"] = [c.replace(" ", "").upper() for c in codes]

    years = _YEAR_RE.findall(prompt)
    if years:
        mentions["academic_year"] = years[0]

    sem = _SEMESTER_RE.search(prompt)
    if sem:
        mentions["semester"] = sem.group(2)

    return mentions


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


async def resolve_context(
    db: AsyncSession,
    user: User,
    prompt: str,
    workspace_context: dict[str, Any] | None = None,
    conversation_context: dict[str, Any] | None = None,
) -> ResolvedContext:
    """Resolve the full context for a user request.

    Parameters
    ----------
    db:                   Database session.
    user:                 Authenticated user from the JWT.
    prompt:               Raw natural-language prompt.
    workspace_context:    Context hints sent by the frontend
                          (e.g. {module_id, programme_id, academic_year}).
    conversation_context: Resolved context from a previous turn stored
                          in session history.
    """
    ctx = ResolvedContext()
    ctx.user_id = user.id
    ctx.user_name = getattr(user, "full_name", "") or getattr(user, "email", "")
    ctx.role = user.role

    ws = workspace_context or {}
    conv = conversation_context or {}
    mentions = _extract_mentions(prompt)

    # ── 1. Institution ───────────────────────────────────────────────────────
    inst: Institution | None = None
    if user.role != UserRole.SYSTEM_ADMIN and user.institution_id:
        inst = await db.get(Institution, user.institution_id)
    elif ws.get("institution_id"):
        inst = await db.get(Institution, uuid.UUID(str(ws["institution_id"])))
    elif conv.get("institution_id"):
        inst = await db.get(Institution, uuid.UUID(str(conv["institution_id"])))

    if inst:
        ctx.institution_id = inst.id
        ctx.institution_name = inst.name
        ctx.institution_code = inst.code

    # ── 2. Module (highest priority entity — explicit code mention) ──────────
    if mentions.get("module_codes") and ctx.institution_id:
        for code in mentions["module_codes"]:
            stmt = select(Module).where(
                and_(
                    Module.code.ilike(code),
                    Module.institution_id == ctx.institution_id,
                )
            )
            result = await db.execute(stmt)
            mod = result.scalar_one_or_none()
            if mod:
                ctx.module_id = mod.id
                ctx.module_name = mod.name
                ctx.module_code = mod.code
                ctx.resolution_source = "explicit"
                break

    # Workspace / conversation module fallback
    if not ctx.module_id:
        mid = ws.get("module_id") or conv.get("module_id")
        if mid:
            mod = await db.get(Module, uuid.UUID(str(mid)))
            if mod and (user.role == UserRole.SYSTEM_ADMIN or mod.institution_id == ctx.institution_id):
                ctx.module_id = mod.id
                ctx.module_name = mod.name
                ctx.module_code = mod.code
                ctx.resolution_source = "workspace" if ws.get("module_id") else "conversation"

    # ── 3. Programme ─────────────────────────────────────────────────────────
    if not ctx.programme_id:
        pid = ws.get("programme_id") or conv.get("programme_id")
        if pid:
            prog = await db.get(Programme, uuid.UUID(str(pid)))
            if prog and (user.role == UserRole.SYSTEM_ADMIN or prog.institution_id == ctx.institution_id):
                ctx.programme_id = prog.id
                ctx.programme_name = prog.name
                ctx.programme_code = getattr(prog, "code", "")
                if ctx.resolution_source == "explicit":
                    pass  # module already explicit
                else:
                    ctx.resolution_source = "workspace" if ws.get("programme_id") else "conversation"

    # If module resolved, infer programme from it
    if ctx.module_id and not ctx.programme_id:
        stmt = select(Module).where(Module.id == ctx.module_id)
        r = await db.execute(stmt)
        mod_full = r.scalar_one_or_none()
        if mod_full and getattr(mod_full, "programme_id", None):
            prog = await db.get(Programme, mod_full.programme_id)
            if prog:
                ctx.programme_id = prog.id
                ctx.programme_name = prog.name
                ctx.programme_code = getattr(prog, "code", "")

    # ── 4. Department ────────────────────────────────────────────────────────
    if not ctx.department_id:
        did = ws.get("department_id") or conv.get("department_id")
        if did:
            dept = await db.get(Department, uuid.UUID(str(did)))
            if dept:
                ctx.department_id = dept.id
                ctx.department_name = dept.name

    # If programme resolved, infer department
    if ctx.programme_id and not ctx.department_id:
        stmt = select(Programme).where(Programme.id == ctx.programme_id)
        r = await db.execute(stmt)
        prog_full = r.scalar_one_or_none()
        if prog_full and getattr(prog_full, "department_id", None):
            dept = await db.get(Department, prog_full.department_id)
            if dept:
                ctx.department_id = dept.id
                ctx.department_name = dept.name

    # ── 5. Faculty ───────────────────────────────────────────────────────────
    if not ctx.faculty_id:
        fid = ws.get("faculty_id") or conv.get("faculty_id")
        if fid:
            fac = await db.get(Faculty, uuid.UUID(str(fid)))
            if fac:
                ctx.faculty_id = fac.id
                ctx.faculty_name = fac.name

    if ctx.department_id and not ctx.faculty_id:
        stmt = select(Department).where(Department.id == ctx.department_id)
        r = await db.execute(stmt)
        dept_full = r.scalar_one_or_none()
        if dept_full and getattr(dept_full, "faculty_id", None):
            fac = await db.get(Faculty, dept_full.faculty_id)
            if fac:
                ctx.faculty_id = fac.id
                ctx.faculty_name = fac.name

    # ── 6. Academic period ───────────────────────────────────────────────────
    ctx.academic_year = (
        mentions.get("academic_year")
        or ws.get("academic_year", "")
        or conv.get("academic_year", "")
    )
    ctx.semester = (
        mentions.get("semester", "")
        or ws.get("semester", "")
        or conv.get("semester", "")
    )

    # ── 7. Applicable frameworks (institution-scoped) ─────────────────────────
    if ctx.institution_id:
        stmt = select(QualityFramework).where(
            and_(
                QualityFramework.is_active.is_(True),
                or_(
                    QualityFramework.institution_id.is_(None),
                    QualityFramework.institution_id == ctx.institution_id,
                ),
            )
        )
        r = await db.execute(stmt)
        frameworks = r.scalars().all()
        ctx.applicable_framework_ids = [f.id for f in frameworks]
        ctx.applicable_framework_codes = [f.code for f in frameworks]

    # ── 8. Open findings (scoped to resolved module/programme) ───────────────
    if ctx.institution_id:
        finding_stmt = (
            select(AuditFinding)
            .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
            .where(
                and_(
                    AuditRun.institution_id == ctx.institution_id,
                    AuditFinding.status.notin_(
                        [FindingStatus.CLOSED]
                    ),
                )
            )
        )
        if ctx.module_id:
            finding_stmt = finding_stmt.where(AuditRun.module_id == ctx.module_id)
        elif ctx.programme_id:
            finding_stmt = finding_stmt.where(AuditRun.programme_id == ctx.programme_id)
        finding_stmt = finding_stmt.limit(200)
        r = await db.execute(finding_stmt)
        findings = r.scalars().all()
        ctx.open_finding_ids = [f.id for f in findings]
        ctx.open_finding_count = len(findings)

    # ── 9. Confidence ────────────────────────────────────────────────────────
    if ctx.resolution_source == "explicit":
        ctx.confidence = 0.95
    elif ctx.resolution_source == "workspace":
        ctx.confidence = 0.90
    elif ctx.resolution_source == "conversation":
        ctx.confidence = 0.80
    else:
        ctx.confidence = 0.70

    # ── 10. Missing context warnings ─────────────────────────────────────────
    if not ctx.institution_id and user.role != UserRole.SYSTEM_ADMIN:
        ctx.missing_context.append("institution")
        ctx.requires_clarification = True
        ctx.clarification_question = "Which institution should I use for this query?"

    return ctx
