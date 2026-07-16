from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.auth import CurrentUser
from app.keycloak import admin as kc
from app.models.audit_log import AuditLog
from app.schemas.user import UserInvite, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_read(kc_user: dict) -> UserRead:
    return UserRead(
        id=kc_user["id"],
        username=kc_user.get("username", ""),
        email=kc_user.get("email", ""),
        firstName=kc_user.get("firstName", ""),
        lastName=kc_user.get("lastName", ""),
        enabled=kc_user.get("enabled", True),
        emailVerified=kc_user.get("emailVerified", False),
    )


async def _log(db, actor: CurrentUser, action: str, target: dict | None = None, details: dict | None = None) -> None:
    entry = AuditLog(
        actor_subject=actor.sub,
        actor_email=actor.email,
        action=action,
        target_user_id=target.get("id") if target else None,
        target_user_email=target.get("email") if target else None,
        details=details,
    )
    db.add(entry)
    await db.commit()


@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: CurrentUser,
    search: str = "",
    first: int = 0,
    max: int = 50,
) -> list[UserRead]:
    users = await kc.list_users(search=search, first=first, max=max)
    return [_to_user_read(u) for u in users]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    body: UserInvite,
    current_user: CurrentUser,
) -> UserRead:
    from app.db.session import AsyncSessionLocal

    user_id = await kc.create_user(
        username=body.username,
        email=str(body.email),
        first_name=body.first_name,
        last_name=body.last_name,
        enabled=True,
    )
    await kc.send_invite(user_id)
    kc_user = await kc.get_user(user_id)

    async with AsyncSessionLocal() as session:
        await _log(
            session,
            current_user,
            "user.invite",
            kc_user,
            {"email": str(body.email)},
        )

    return _to_user_read(kc_user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str, current_user: CurrentUser) -> UserRead:
    try:
        kc_user = await kc.get_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_read(kc_user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: CurrentUser,
) -> UserRead:
    patch = body.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")
    await kc.update_user(user_id, patch)
    kc_user = await kc.get_user(user_id)

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await _log(session, current_user, "user.update", kc_user, patch)

    return _to_user_read(kc_user)


@router.post("/{user_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_user(user_id: str, current_user: CurrentUser) -> None:
    kc_user = await kc.get_user(user_id)
    await kc.disable_user(user_id)

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await _log(session, current_user, "user.disable", kc_user)


@router.post("/{user_id}/enable", status_code=status.HTTP_204_NO_CONTENT)
async def enable_user(user_id: str, current_user: CurrentUser) -> None:
    kc_user = await kc.get_user(user_id)
    await kc.enable_user(user_id)

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await _log(session, current_user, "user.enable", kc_user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(user_id: str, current_user: CurrentUser) -> None:
    kc_user = await kc.get_user(user_id)
    await kc.reset_password_email(user_id)

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await _log(session, current_user, "user.reset_password", kc_user)
