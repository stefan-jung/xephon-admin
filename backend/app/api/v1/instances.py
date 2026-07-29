from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.instance import Instance
from app.schemas.instance import InstanceCreate, InstanceHealthRead, InstanceRead, InstanceUpdate

router = APIRouter(prefix="/instances", tags=["instances"])


@router.get("", response_model=list[InstanceRead])
async def list_instances(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[InstanceRead]:
    result = await db.execute(select(Instance).order_by(Instance.name))
    return list(result.scalars().all())


@router.post("", response_model=InstanceRead, status_code=status.HTTP_201_CREATED)
async def create_instance(
    body: InstanceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InstanceRead:
    instance = Instance(
        name=body.name,
        type=body.type,
        base_url=body.base_url,
        enabled_services=body.enabled_services,
        health_status=body.health_status,
        cms_url=body.cms_url,
        pm_url=body.pm_url,
        pim_url=body.pim_url,
        erp_url=body.erp_url,
        ai_url=body.ai_url,
    )
    db.add(instance)
    await db.flush()
    db.add(
        AuditLog(
            actor_subject=current_user.sub,
            actor_email=current_user.email,
            action="instance.create",
            details={"id": str(instance.id), "name": body.name, "type": body.type},
        )
    )
    await db.commit()
    await db.refresh(instance)
    return instance


@router.get("/{instance_id}", response_model=InstanceRead)
async def get_instance(
    instance_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InstanceRead:
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance


@router.get("/{instance_id}/health", response_model=InstanceHealthRead)
async def get_instance_health(
    instance_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InstanceHealthRead:
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return InstanceHealthRead(
        instance_id=instance.id,
        health_status=instance.health_status,
        services=instance.health,
    )


@router.patch("/{instance_id}", response_model=InstanceRead)
async def update_instance(
    instance_id: uuid.UUID,
    body: InstanceUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InstanceRead:
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    patch = body.model_dump(exclude_none=True)
    for key, val in patch.items():
        setattr(instance, key, val)
    db.add(
        AuditLog(
            actor_subject=current_user.sub,
            actor_email=current_user.email,
            action="instance.update",
            details={"id": str(instance_id), **patch},
        )
    )
    await db.commit()
    await db.refresh(instance)
    return instance


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instance(
    instance_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    await db.delete(instance)
    db.add(
        AuditLog(
            actor_subject=current_user.sub,
            actor_email=current_user.email,
            action="instance.delete",
            details={"id": str(instance_id)},
        )
    )
    await db.commit()
