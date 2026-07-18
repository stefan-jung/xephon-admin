from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from httpx import AsyncClient

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
    """Sync factory returning an async context manager that no-ops the audit write."""
    session = MagicMock()
    session.commit = AsyncMock()
    outer = MagicMock()
    outer.return_value.__aenter__ = AsyncMock(return_value=session)
    outer.return_value.__aexit__ = AsyncMock(return_value=False)
    return outer


async def test_list_users(client: AsyncClient) -> None:
    with patch("app.api.v1.users.kc") as kc:
        kc.list_users = AsyncMock(return_value=[_KC_USER])
        r = await client.get("/users")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["email"] == "jdoe@example.com"
    assert data[0]["username"] == "jdoe"


async def test_list_users_search_returns_empty(client: AsyncClient) -> None:
    with patch("app.api.v1.users.kc") as kc:
        kc.list_users = AsyncMock(return_value=[])
        r = await client.get("/users", params={"search": "nobody"})
    assert r.status_code == 200
    assert r.json() == []


async def test_get_user(client: AsyncClient) -> None:
    with patch("app.api.v1.users.kc") as kc:
        kc.get_user = AsyncMock(return_value=_KC_USER)
        r = await client.get("/users/user-uuid-1")
    assert r.status_code == 200
    assert r.json()["username"] == "jdoe"


async def test_get_user_not_found(client: AsyncClient) -> None:
    with patch("app.api.v1.users.kc") as kc:
        kc.get_user = AsyncMock(
            side_effect=httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock())
        )
        r = await client.get("/users/ghost-id")
    assert r.status_code == 404


async def test_invite_user(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.users.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.create_user = AsyncMock(return_value="user-uuid-1")
        kc.send_invite = AsyncMock()
        kc.get_user = AsyncMock(return_value=_KC_USER)
        r = await client.post(
            "/users",
            json={
                "username": "jdoe",
                "email": "jdoe@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "jdoe@example.com"
    assert data["username"] == "jdoe"


async def test_update_user(client: AsyncClient) -> None:
    updated = {**_KC_USER, "firstName": "Jane"}
    with (
        patch("app.api.v1.users.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.update_user = AsyncMock()
        kc.get_user = AsyncMock(return_value=updated)
        r = await client.patch("/users/user-uuid-1", json={"firstName": "Jane"})
    assert r.status_code == 200
    assert r.json()["firstName"] == "Jane"


async def test_update_user_no_fields_returns_400(client: AsyncClient) -> None:
    r = await client.patch("/users/user-uuid-1", json={})
    assert r.status_code == 400


async def test_disable_user(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.users.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.get_user = AsyncMock(return_value=_KC_USER)
        kc.disable_user = AsyncMock()
        r = await client.post("/users/user-uuid-1/disable")
    assert r.status_code == 204


async def test_enable_user(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.users.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.get_user = AsyncMock(return_value=_KC_USER)
        kc.enable_user = AsyncMock()
        r = await client.post("/users/user-uuid-1/enable")
    assert r.status_code == 204


async def test_reset_password(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.users.kc") as kc,
        patch("app.db.session.AsyncSessionLocal", _mock_sl()),
    ):
        kc.get_user = AsyncMock(return_value=_KC_USER)
        kc.reset_password_email = AsyncMock()
        r = await client.post("/users/user-uuid-1/reset-password")
    assert r.status_code == 204
