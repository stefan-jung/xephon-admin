from __future__ import annotations

from fastapi import APIRouter

from app.core.auth import CurrentUser
from app.db.session import AsyncSessionLocal
from app.keycloak import admin as kc
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[dict])
async def list_realm_roles(current_user: CurrentUser) -> list[dict]:
    roles = await kc.list_realm_roles()
    return [
        {"id": r["id"], "name": r["name"], "description": r.get("description", "")} for r in roles
    ]


@router.get("/users/{user_id}", response_model=list[dict])
async def get_user_roles(user_id: str, current_user: CurrentUser) -> list[dict]:
    roles = await kc.get_user_realm_roles(user_id)
    return [
        {"id": r["id"], "name": r["name"], "description": r.get("description", "")} for r in roles
    ]


@router.post("/users/{user_id}/{role_name}", status_code=204)
async def assign_role(user_id: str, role_name: str, current_user: CurrentUser) -> None:
    await kc.assign_realm_role(user_id, role_name)
    kc_user = await kc.get_user(user_id)

    async with AsyncSessionLocal() as session:
        session.add(
            AuditLog(
                actor_subject=current_user.sub,
                actor_email=current_user.email,
                action="role.assign",
                target_user_id=user_id,
                target_user_email=kc_user.get("email"),
                details={"role": role_name},
            )
        )
        await session.commit()


@router.delete("/users/{user_id}/{role_name}", status_code=204)
async def remove_role(user_id: str, role_name: str, current_user: CurrentUser) -> None:
    await kc.remove_realm_role(user_id, role_name)
    kc_user = await kc.get_user(user_id)

    async with AsyncSessionLocal() as session:
        session.add(
            AuditLog(
                actor_subject=current_user.sub,
                actor_email=current_user.email,
                action="role.remove",
                target_user_id=user_id,
                target_user_email=kc_user.get("email"),
                details={"role": role_name},
            )
        )
        await session.commit()
