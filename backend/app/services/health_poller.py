"""Background job that keeps each registered Instance's per-service
health snapshot current -- see ROADMAP.md's "Health monitoring" entry
and Instance's own docstring for the exact shape stored.

`poll_once` (one full pass over every Instance/service URl) is kept
separate from `poll_loop` (the forever-sleep-30s wrapper actually
started from main.py's lifespan) so tests can exercise a single,
deterministic poll cycle without waiting on a real timer.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.instance import Instance

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
_REQUEST_TIMEOUT_SECONDS = 5.0

# Service name (as stored in Instance.health / enabled_services) -> the
# Instance column holding that service's base URL.
_SERVICE_URL_FIELDS: dict[str, str] = {
    "cms": "cms_url",
    "pm": "pm_url",
    "pim": "pim_url",
    "erp": "erp_url",
    "ai": "ai_url",
}


async def _check_one(client: httpx.AsyncClient, base_url: str) -> tuple[str, float | None]:
    """Returns (status, latency_ms). status is "up" only for a 200 from
    `{base_url}/health/live`; a non-200, timeout, or connection error is
    "down" -- a service that hasn't implemented that endpoint yet is
    indistinguishable from one that's actually unreachable, which is the
    honest behavior until every service implements the documented
    liveness contract (see ROADMAP.md's note on this).
    """
    start = time.monotonic()
    try:
        response = await client.get(
            f"{base_url.rstrip('/')}/health/live", timeout=_REQUEST_TIMEOUT_SECONDS
        )
        latency_ms = (time.monotonic() - start) * 1000
        return ("up" if response.status_code == 200 else "down"), latency_ms
    except httpx.HTTPError:
        return "down", None


def _next_snapshot(
    previous: dict[str, Any] | None, status: str, latency_ms: float | None
) -> dict[str, Any]:
    prev_status = (previous or {}).get("status")
    prev_streak = (previous or {}).get("streak", 0)
    streak = prev_streak + 1 if prev_status == status else 1
    return {
        "status": status,
        "checked_at": datetime.now(UTC).isoformat(),
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "streak": streak,
    }


def _overall_status(services: dict[str, Any]) -> str:
    if not services:
        return "unknown"
    statuses = {entry["status"] for entry in services.values()}
    if statuses == {"up"}:
        return "up"
    if statuses == {"down"}:
        return "down"
    return "degraded"


async def poll_once(session: AsyncSession, *, client: httpx.AsyncClient | None = None) -> None:
    """Polls every registered Instance's configured service URLs once and
    persists the results (Instance.health + the derived
    Instance.health_status). A service field left unset (None/empty) is
    dropped from the stored snapshot rather than checked -- only
    *registered* services are polled, per the ROADMAP wording.
    """
    owns_client = client is None
    client = client or httpx.AsyncClient()
    try:
        instances = (await session.execute(select(Instance))).scalars().all()
        for instance in instances:
            health: dict[str, Any] = dict(instance.health or {})
            for service_name, field_name in _SERVICE_URL_FIELDS.items():
                base_url = getattr(instance, field_name)
                if not base_url:
                    health.pop(service_name, None)
                    continue
                status, latency_ms = await _check_one(client, base_url)
                health[service_name] = _next_snapshot(health.get(service_name), status, latency_ms)
            instance.health = health
            instance.health_status = _overall_status(health)
        await session.commit()
    finally:
        if owns_client:
            await client.aclose()


async def poll_loop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Runs poll_once every POLL_INTERVAL_SECONDS until cancelled --
    started as a background asyncio task from main.py's lifespan, and
    cancelled (via task.cancel()) on shutdown. A single cycle's failure
    (a bug here, not a polled service being down -- that's just "down"
    status, not an exception) is logged and skipped rather than killing
    the loop, since one bad cycle shouldn't stop future ones.
    """
    while True:
        try:
            async with session_factory() as session:
                await poll_once(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Health poll cycle failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
