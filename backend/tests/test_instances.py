from __future__ import annotations

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture(autouse=True)
async def _clean_instances(db_session: AsyncSession) -> None:
    """Delete all instances rows at the start of each test; rolled back after."""
    await db_session.execute(text("DELETE FROM instances"))
    await db_session.flush()


async def test_list_instances_empty(client: AsyncClient) -> None:
    r = await client.get("/instances")
    assert r.status_code == 200
    assert r.json() == []


async def test_create_instance(client: AsyncClient) -> None:
    r = await client.post(
        "/instances",
        json={
            "name": "Acme Private Cloud",
            "type": "private",
            "base_url": "https://acme.xephon.example",
            "enabled_services": ["cms", "pm"],
            "cms_url": "https://cms.acme.xephon.example",
            "pm_url": "https://pm.acme.xephon.example",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Acme Private Cloud"
    assert data["type"] == "private"
    assert data["base_url"] == "https://acme.xephon.example"
    assert data["enabled_services"] == ["cms", "pm"]
    assert data["health_status"] == "unknown"
    assert data["cms_url"] == "https://cms.acme.xephon.example"
    assert data["pm_url"] == "https://pm.acme.xephon.example"
    assert data["pim_url"] is None
    assert data["erp_url"] is None
    assert data["ai_url"] is None
    assert data["id"]


async def test_create_instance_defaults(client: AsyncClient) -> None:
    r = await client.post("/instances", json={"name": "Minimal", "type": "saas"})
    assert r.status_code == 201
    data = r.json()
    assert data["base_url"] == ""
    assert data["enabled_services"] == []
    assert data["health_status"] == "unknown"


async def test_create_instance_rejects_invalid_type(client: AsyncClient) -> None:
    r = await client.post("/instances", json={"name": "Bad", "type": "on-prem"})
    assert r.status_code == 422


async def test_get_instance(client: AsyncClient) -> None:
    created = (
        await client.post("/instances", json={"name": "Enterprise Co", "type": "enterprise"})
    ).json()
    r = await client.get(f"/instances/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Enterprise Co"


async def test_get_instance_not_found(client: AsyncClient) -> None:
    r = await client.get("/instances/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_instances_after_creates(client: AsyncClient) -> None:
    await client.post("/instances", json={"name": "Instance A", "type": "saas"})
    await client.post("/instances", json={"name": "Instance B", "type": "private"})
    r = await client.get("/instances")
    assert r.status_code == 200
    names = [i["name"] for i in r.json()]
    assert "Instance A" in names
    assert "Instance B" in names


async def test_update_instance_health_status_and_urls(client: AsyncClient) -> None:
    created = (await client.post("/instances", json={"name": "SaaS Main", "type": "saas"})).json()
    r = await client.patch(
        f"/instances/{created['id']}",
        json={"health_status": "healthy", "erp_url": "https://erp.example"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["health_status"] == "healthy"
    assert data["erp_url"] == "https://erp.example"
    assert data["name"] == "SaaS Main"  # untouched fields survive a partial patch


async def test_update_instance_not_found(client: AsyncClient) -> None:
    r = await client.patch(
        "/instances/00000000-0000-0000-0000-000000000000", json={"name": "Ghost"}
    )
    assert r.status_code == 404


async def test_delete_instance(client: AsyncClient) -> None:
    created = (await client.post("/instances", json={"name": "Temp", "type": "saas"})).json()
    r = await client.delete(f"/instances/{created['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/instances/{created['id']}")
    assert r2.status_code == 404


async def test_delete_instance_not_found(client: AsyncClient) -> None:
    r = await client.delete("/instances/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
