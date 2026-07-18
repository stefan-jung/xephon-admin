from __future__ import annotations

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


@pytest_asyncio.fixture(autouse=True)
async def _clean_audit_log(db_session: AsyncSession) -> None:
    await db_session.execute(text("DELETE FROM audit_log"))
    await db_session.flush()


async def _seed(session: AsyncSession, **kwargs: object) -> AuditLog:
    entry = AuditLog(
        actor_subject=kwargs.get("actor_subject", "sub-default"),  # type: ignore[arg-type]
        actor_email=kwargs.get("actor_email", "actor@example.com"),  # type: ignore[arg-type]
        action=kwargs.get("action", "service.create"),  # type: ignore[arg-type]
        target_user_id=kwargs.get("target_user_id"),  # type: ignore[arg-type]
        target_user_email=kwargs.get("target_user_email"),  # type: ignore[arg-type]
        details=kwargs.get("details"),  # type: ignore[arg-type]
    )
    session.add(entry)
    await session.flush()
    return entry


async def test_list_audit_empty(client: AsyncClient) -> None:
    r = await client.get("/audit")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["items"] == []


async def test_list_audit_returns_inserted_rows(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, action="service.create", details={"slug": "xephon-pm"})
    await _seed(db_session, action="user.invite", actor_subject="admin-2")
    r = await client.get("/audit")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    actions = {item["action"] for item in data["items"]}
    assert actions == {"service.create", "user.invite"}


async def test_list_audit_filter_by_action(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed(db_session, action="service.create")
    await _seed(db_session, action="user.disable")
    r = await client.get("/audit", params={"action": "service"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "service.create"


async def test_list_audit_filter_by_actor(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed(db_session, actor_subject="alice", action="service.create")
    await _seed(db_session, actor_subject="bob", action="service.delete")
    r = await client.get("/audit", params={"actor": "alice"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["actor_subject"] == "alice"


async def test_list_audit_filter_by_target_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    uid = "user-abc-123"
    await _seed(db_session, target_user_id=uid, action="user.disable")
    await _seed(db_session, target_user_id="other", action="user.enable")
    r = await client.get("/audit", params={"target_user_id": uid})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["target_user_id"] == uid


async def test_list_audit_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    for i in range(5):
        await _seed(db_session, action=f"action.{i}")
    r = await client.get("/audit", params={"page": 1, "page_size": 2})
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    r2 = await client.get("/audit", params={"page": 2, "page_size": 2})
    data2 = r2.json()
    assert len(data2["items"]) == 2

    r3 = await client.get("/audit", params={"page": 3, "page_size": 2})
    data3 = r3.json()
    assert len(data3["items"]) == 1


async def test_list_audit_action_contains_match(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, action="role.assign")
    await _seed(db_session, action="role.remove")
    await _seed(db_session, action="user.invite")
    r = await client.get("/audit", params={"action": "role"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
