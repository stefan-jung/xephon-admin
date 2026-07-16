from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from fastapi import Depends
from app.models.audit_log import AuditLog
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceRead])
async def list_services(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    result = await db.execute(select(Service).order_by(Service.slug))
    return list(result.scalars().all())


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    existing = await db.get(Service, body.slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Service '{body.slug}' already exists")
    svc = Service(
        slug=body.slug,
        name=body.name,
        base_url=body.base_url,
        enabled=body.enabled,
        roles=body.roles,
    )
    db.add(svc)
    db.add(AuditLog(
        actor_subject=current_user.sub,
        actor_email=current_user.email,
        action="service.create",
        details={"slug": body.slug, "name": body.name},
    ))
    await db.commit()
    await db.refresh(svc)
    return svc


@router.get("/{slug}", response_model=ServiceRead)
async def get_service(
    slug: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    svc = await db.get(Service, slug)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.patch("/{slug}", response_model=ServiceRead)
async def update_service(
    slug: str,
    body: ServiceUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    svc = await db.get(Service, slug)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    patch = body.model_dump(exclude_none=True)
    for key, val in patch.items():
        setattr(svc, key, val)
    db.add(AuditLog(
        actor_subject=current_user.sub,
        actor_email=current_user.email,
        action="service.update",
        details={"slug": slug, **patch},
    ))
    await db.commit()
    await db.refresh(svc)
    return svc


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    slug: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = await db.get(Service, slug)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.delete(svc)
    db.add(AuditLog(
        actor_subject=current_user.sub,
        actor_email=current_user.email,
        action="service.delete",
        details={"slug": slug},
    ))
    await db.commit()
