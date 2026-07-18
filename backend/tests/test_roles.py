from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

_FAKE_ROLES = [
    {"id": "role-1", "name": "xephon:admin", "description": "Admin role"},
    {"id": "role-2", "name": "xephon:user", "description": "User role"},
]

_KC_USER = {
    "id": "user-uuid-1",
    "username": "jdoe",
    "email": "jdoe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "enabled": True,
    "emailVerified": True,
}


def _mock_sl() -> MagicMock:
    session = MagicMock()
    session.commit = AsyncMock()
    outer = MagicMock()
    outer.return_value.__aenter__ = AsyncMock(return_value=session)
    outer.return_value.__aexit__ = AsyncMock(return_value=False)
    return outer


async def test_list_realm_roles(client: AsyncClient) -> None:
    with patch("app.api.v1.roles.kc") as kc:
        kc.list_realm_roles = AsyncMock(return_value=_FAKE_ROLES)
        r = await client.get("/roles")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    names = [d["name"] for d in data]
    assert "xephon:admin" in names
    assert "xephon:user" in names


async def test_list_realm_roles_includes_description(client: AsyncClient) -> None:
    with patch("app.api.v1.roles.kc") as kc:
        kc.list_realm_roles = AsyncMock(return_value=_FAKE_ROLES)
        r = await client.get("/roles")
    data = r.json()
    assert data[0]["description"] == "Admin role"


async def test_get_user_roles(client: AsyncClient) -> None:
    with patch("app.api.v1.roles.kc") as kc:
        kc.get_user_realm_roles = AsyncMock(return_value=[_FAKE_ROLES[0]])
        r = await client.get("/roles/users/user-uuid-1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "xephon:admin"


async def test_get_user_roles_empty(client: AsyncClient) -> None:
    with patch("app.api.v1.roles.kc") as kc:
        kc.get_user_realm_roles = AsyncMock(return_value=[])
        r = await client.get("/roles/users/user-uuid-1")
    assert r.status_code == 200
    assert r.json() == []


async def test_assign_role(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.roles.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.assign_realm_role = AsyncMock()
        kc.get_user = AsyncMock(return_value=_KC_USER)
        r = await client.post("/roles/users/user-uuid-1/xephon:user")
    assert r.status_code == 204


async def test_remove_role(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.roles.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.remove_realm_role = AsyncMock()
        kc.get_user = AsyncMock(return_value=_KC_USER)
        r = await client.delete("/roles/users/user-uuid-1/xephon:user")
    assert r.status_code == 204
