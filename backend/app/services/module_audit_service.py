"""Module Folder Audit service — CRUD + compliance calculation."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.services import audit_history_service
from app.models.department import Department
from app.models.enums import ChecklistItemStatus, ModuleAuditStatus, UserRole
from app.models.faculty import Faculty
from app.models.module import Module
from app.models.module_audit import CHECKLIST_ITEMS, AuditChecklistItem, ModuleAudit
from app.models.programme import Programme
from app.models.user import User
from app.schemas.module_audit import ModuleAuditCreate, ModuleAuditUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _calc_status(pct: float, is_draft: bool) -> ModuleAuditStatus:
    if is_draft:
        return ModuleAuditStatus.DRAFT
    if pct >= 90:
        return ModuleAuditStatus.COMPLIANT
    if pct >= 70:
        return ModuleAuditStatus.AT_RISK
    return ModuleAuditStatus.NON_COMPLIANT


def _recalculate(audit: ModuleAudit) -> None:
    """Recompute counts and compliance_percentage from checklist items.
    Assumes items are already loaded (not lazy)."""
    items = audit.checklist_items  # type: ignore[attr-defined]
    total = len(items)
    compliant = sum(1 for i in items if i.status == ChecklistItemStatus.COMPLIANT)
    missing = sum(1 for i in items if i.status == ChecklistItemStatus.MISSING)
    partial = sum(1 for i in items if i.status == ChecklistItemStatus.PARTIAL)
    na = sum(1 for i in items if i.status == ChecklistItemStatus.NOT_APPLICABLE)

    # Denominator excludes N/A items
    denominator = total - na
    pct = (compliant + partial * 0.5) / denominator * 100 if denominator > 0 else 0.0

    audit.total_items = total
    audit.compliant_count = compliant
    audit.missing_count = missing
    audit.partial_count = partial
    audit.not_applicable_count = na
    audit.compliance_percentage = round(pct, 2)

    # Only move out of DRAFT when all items are set away from default MISSING
    is_draft = audit.status == ModuleAuditStatus.DRAFT and all(
        i.status == ChecklistItemStatus.MISSING for i in items
    )
    if not is_draft:
        audit.status = _calc_status(pct, is_draft=False)


async def _resolve_module_hierarchy(
    db: AsyncSession, module_id: uuid.UUID
) -> tuple[Module, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    """Return (module, programme_id, department_id, faculty_id, institution_id)."""
    result = await db.execute(
        select(Module, Programme.id, Department.id, Faculty.id, Faculty.institution_id)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Module.id == module_id)
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Module", module_id)
    return row  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_audit(
    db: AsyncSession,
    data: ModuleAuditCreate,
    current_user: User,
) -> ModuleAudit:
    module, prog_id, dept_id, fac_id, inst_id = await _resolve_module_hierarchy(
        db, data.module_id
    )

    # Tenant check
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and current_user.institution_id != inst_id
    ):
        raise ConflictError("You may only create audits within your own institution.")

    audit = ModuleAudit(
        module_id=data.module_id,
        programme_id=prog_id,
        department_id=dept_id,
        faculty_id=fac_id,
        institution_id=inst_id,
        auditor_id=current_user.id,
        academic_year=data.academic_year,
        notes=data.notes,
        status=ModuleAuditStatus.DRAFT,
        total_items=len(CHECKLIST_ITEMS),
        missing_count=len(CHECKLIST_ITEMS),
        compliance_percentage=0.0,
    )
    db.add(audit)
    await db.flush()  # get audit.id

    for key, label in CHECKLIST_ITEMS:
        db.add(AuditChecklistItem(
            audit_id=audit.id,
            item_key=key,
            item_label=label,
            status=ChecklistItemStatus.MISSING,
            evidence_required=True,
        ))

    # Record history: created
    await audit_history_service.record_created(
        db, audit.id, current_user.id, module.code
    )
    await db.commit()
    return await get_audit(db, audit.id)


async def get_audit(db: AsyncSession, audit_id: uuid.UUID) -> ModuleAudit:
    result = await db.execute(
        select(ModuleAudit)
        .options(selectinload(ModuleAudit.checklist_items))
        .where(ModuleAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise NotFoundError("ModuleAudit", audit_id)
    return audit


async def list_audits(
    db: AsyncSession,
    current_user: User,
    module_id: uuid.UUID | None = None,
    institution_id: uuid.UUID | None = None,
    status: ModuleAuditStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ModuleAudit]:
    q = select(ModuleAudit).options(selectinload(ModuleAudit.checklist_items))

    if current_user.role != UserRole.SYSTEM_ADMIN:
        q = q.where(ModuleAudit.institution_id == current_user.institution_id)
    elif institution_id:
        q = q.where(ModuleAudit.institution_id == institution_id)

    # Lecturers see only audits for their own modules
    if current_user.role == UserRole.LECTURER:
        lecturer_modules = (
            await db.execute(
                select(Module.id).where(Module.lecturer_id == current_user.id)
            )
        ).scalars().all()
        q = q.where(ModuleAudit.module_id.in_(lecturer_modules))

    if module_id:
        q = q.where(ModuleAudit.module_id == module_id)
    if status:
        q = q.where(ModuleAudit.status == status)

    q = q.order_by(ModuleAudit.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_audit(
    db: AsyncSession,
    audit: ModuleAudit,
    data: ModuleAuditUpdate,
    actor_id: uuid.UUID | None = None,
) -> ModuleAudit:
    notes_changed = data.notes is not None and data.notes != audit.notes
    if data.notes is not None:
        audit.notes = data.notes

    old_pct = audit.compliance_percentage
    old_status = audit.status.value

    # Apply checklist updates
    if data.checklist:
        existing = {item.item_key: item for item in audit.checklist_items}  # type: ignore[attr-defined]
        for key, item_data in data.checklist.items():
            if key in existing:
                old_item_status = existing[key].status.value
                existing[key].status = item_data.status
                existing[key].comment = item_data.comment
                existing[key].evidence_required = item_data.evidence_required
                # Record per-item history
                await audit_history_service.record_checklist_updated(
                    db, audit.id, actor_id,
                    existing[key].item_label, old_item_status, item_data.status.value,
                )

        result = await db.execute(
            select(AuditChecklistItem).where(AuditChecklistItem.audit_id == audit.id)
        )
        audit.checklist_items = list(result.scalars().all())  # type: ignore[assignment]
        _recalculate(audit)

        # Record compliance and status changes
        if audit.compliance_percentage != old_pct:
            await audit_history_service.record_compliance_changed(
                db, audit.id, actor_id, old_pct, audit.compliance_percentage, audit.status.value,
            )
        if audit.status.value != old_status:
            await audit_history_service.record_status_changed(
                db, audit.id, actor_id, old_status, audit.status.value,
            )

    if notes_changed:
        await audit_history_service.record_notes_updated(db, audit.id, actor_id)

    await db.commit()
    return await get_audit(db, audit.id)


async def delete_audit(db: AsyncSession, audit: ModuleAudit) -> None:
    await db.delete(audit)
    await db.commit()
