from __future__ import annotations

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture(autouse=True)
async def _clean_services(db_session: AsyncSession) -> None:
    """Delete all services rows at the start of each test; rolled back after."""
    await db_session.execute(text("DELETE FROM services"))
    await db_session.flush()


async def test_list_services_empty(client: AsyncClient) -> None:
    r = await client.get("/services")
    assert r.status_code == 200
    assert r.json() == []


async def test_create_service(client: AsyncClient) -> None:
    r = await client.post(
        "/services",
        json={
            "slug": "test-pm",
            "name": "Project Manager",
            "base_url": "http://pm.internal",
            "enabled": True,
            "roles": ["xephon:user", "xephon:admin"],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["slug"] == "test-pm"
    assert data["name"] == "Project Manager"
    assert data["base_url"] == "http://pm.internal"
    assert data["enabled"] is True
    assert data["roles"] == ["xephon:user", "xephon:admin"]


async def test_create_service_duplicate_slug(client: AsyncClient) -> None:
    payload = {"slug": "test-dup", "name": "Duplicate Service"}
    await client.post("/services", json=payload)
    r = await client.post("/services", json=payload)
    assert r.status_code == 409


async def test_create_service_defaults(client: AsyncClient) -> None:
    r = await client.post("/services", json={"slug": "test-minimal", "name": "Minimal"})
    assert r.status_code == 201
    data = r.json()
    assert data["enabled"] is True
    assert data["roles"] == []
    assert data["base_url"] == ""


async def test_get_service(client: AsyncClient) -> None:
    await client.post("/services", json={"slug": "test-cms", "name": "CMS"})
    r = await client.get("/services/test-cms")
    assert r.status_code == 200
    assert r.json()["name"] == "CMS"


async def test_get_service_not_found(client: AsyncClient) -> None:
    r = await client.get("/services/does-not-exist")
    assert r.status_code == 404


async def test_list_services_after_creates(client: AsyncClient) -> None:
    await client.post("/services", json={"slug": "test-svc-a", "name": "A"})
    await client.post("/services", json={"slug": "test-svc-b", "name": "B"})
    r = await client.get("/services")
    assert r.status_code == 200
    slugs = [s["slug"] for s in r.json()]
    assert "test-svc-a" in slugs
    assert "test-svc-b" in slugs


async def test_update_service_name_and_enabled(client: AsyncClient) -> None:
    await client.post("/services", json={"slug": "test-erp", "name": "ERP"})
    r = await client.patch("/services/test-erp", json={"name": "ERP v2", "enabled": False})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "ERP v2"
    assert data["enabled"] is False


async def test_update_service_roles(client: AsyncClient) -> None:
    await client.post("/services", json={"slug": "test-pim", "name": "PIM"})
    r = await client.patch("/services/test-pim", json={"roles": ["xephon:editor"]})
    assert r.status_code == 200
    assert r.json()["roles"] == ["xephon:editor"]


async def test_update_service_not_found(client: AsyncClient) -> None:
    r = await client.patch("/services/ghost", json={"name": "Ghost"})
    assert r.status_code == 404


async def test_delete_service(client: AsyncClient) -> None:
    await client.post("/services", json={"slug": "test-tmp", "name": "Tmp"})
    r = await client.delete("/services/test-tmp")
    assert r.status_code == 204
    r2 = await client.get("/services/test-tmp")
    assert r2.status_code == 404


async def test_delete_service_not_found(client: AsyncClient) -> None:
    r = await client.delete("/services/ghost")
    assert r.status_code == 404
