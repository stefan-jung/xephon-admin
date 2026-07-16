from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=dict)
async def list_audit_log(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor: str | None = None,
    action: str | None = None,
    target_user_id: str | None = None,
) -> dict:
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if actor:
        q = q.where(AuditLog.actor_subject == actor)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if target_user_id:
        q = q.where(AuditLog.target_user_id == target_user_id)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [AuditLogRead.model_validate(r) for r in rows],
    }
