"""Health poller (app/services/health_poller.py) -- poll_once against a
real db_session, with outbound HTTP faked via httpx.MockTransport (no
new test dependency needed; matches this repo's existing use of plain
httpx elsewhere) so these never make real network calls.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instance import Instance
from app.services.health_poller import poll_once


def _client_returning(status_code: int) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _client_raising(exc: Exception) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _client_from(responder: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(responder))


async def _make_instance(db_session: AsyncSession, **overrides: object) -> Instance:
    instance = Instance(name="Test Instance", type="saas", **overrides)  # type: ignore[arg-type]
    db_session.add(instance)
    await db_session.flush()
    return instance


async def test_poll_once_marks_service_up_on_200(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["status"] == "up"
    assert instance.health["cms"]["streak"] == 1
    assert instance.health["cms"]["latency_ms"] is not None
    assert instance.health_status == "up"


async def test_poll_once_marks_service_down_on_non_200(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(503) as client:
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["status"] == "down"
    assert instance.health_status == "down"


async def test_poll_once_marks_service_down_on_connection_error(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_raising(httpx.ConnectError("refused")) as client:
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["status"] == "down"
    assert instance.health["cms"]["latency_ms"] is None


async def test_poll_once_streak_increments_on_repeated_status(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)
        await poll_once(db_session, client=client)
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["streak"] == 3


async def test_poll_once_streak_resets_on_status_change(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)
        await poll_once(db_session, client=client)
    assert instance.health["cms"]["streak"] == 2

    async with _client_returning(500) as client:
        await poll_once(db_session, client=client)
    assert instance.health["cms"]["status"] == "down"
    assert instance.health["cms"]["streak"] == 1


async def test_poll_once_overall_status_degraded_when_mixed(db_session: AsyncSession) -> None:
    instance = await _make_instance(
        db_session, cms_url="https://cms.example", pm_url="https://pm.example"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if "cms" in str(request.url):
            return httpx.Response(200)
        return httpx.Response(500)

    async with _client_from(handler) as client:
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["status"] == "up"
    assert instance.health["pm"]["status"] == "down"
    assert instance.health_status == "degraded"


async def test_poll_once_skips_unconfigured_services(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session)
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)

    assert instance.health == {}
    assert instance.health_status == "unknown"


async def test_poll_once_only_polls_configured_services(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)

    assert set(instance.health.keys()) == {"cms"}


async def test_poll_once_removes_service_when_url_cleared(db_session: AsyncSession) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)
    assert "cms" in instance.health

    instance.cms_url = None
    async with _client_returning(200) as client:
        await poll_once(db_session, client=client)
    assert instance.health == {}


async def test_poll_once_requests_health_live_path(db_session: AsyncSession) -> None:
    await _make_instance(db_session, cms_url="https://cms.example/")
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200)

    async with _client_from(handler) as client:
        await poll_once(db_session, client=client)

    assert requested_urls == ["https://cms.example/health/live"]


@pytest.mark.parametrize("exc", [httpx.ConnectTimeout("timed out"), httpx.ReadTimeout("slow")])
async def test_poll_once_treats_timeouts_as_down(db_session: AsyncSession, exc: Exception) -> None:
    instance = await _make_instance(db_session, cms_url="https://cms.example")
    async with _client_raising(exc) as client:
        await poll_once(db_session, client=client)

    assert instance.health["cms"]["status"] == "down"
