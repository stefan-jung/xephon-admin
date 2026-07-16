from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict[str, Any] = {}


async def _get_sa_token() -> str:
    now = time.monotonic()
    if _token_cache.get("expires_at", 0) - now > 30:
        return _token_cache["access_token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_admin_client_id,
                "client_secret": settings.keycloak_admin_client_secret,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 300)
    return data["access_token"]


async def _admin_client() -> httpx.AsyncClient:
    token = await _get_sa_token()
    return httpx.AsyncClient(
        base_url=settings.keycloak_admin_base + "/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )


async def list_users(search: str = "", first: int = 0, max: int = 100) -> list[dict]:
    async with await _admin_client() as client:
        resp = await client.get(
            "users",
            params={"search": search, "first": first, "max": max, "briefRepresentation": "false"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_user(user_id: str) -> dict:
    async with await _admin_client() as client:
        resp = await client.get(f"users/{user_id}")
        resp.raise_for_status()
        return resp.json()


async def create_user(
    username: str,
    email: str,
    first_name: str = "",
    last_name: str = "",
    enabled: bool = True,
) -> str:
    async with await _admin_client() as client:
        resp = await client.post(
            "users",
            json={
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": enabled,
                "emailVerified": False,
            },
        )
        resp.raise_for_status()
        location = resp.headers.get("Location", "")
        return location.rsplit("/", 1)[-1]


async def update_user(user_id: str, patch: dict) -> None:
    async with await _admin_client() as client:
        resp = await client.put(f"users/{user_id}", json=patch)
        resp.raise_for_status()


async def disable_user(user_id: str) -> None:
    await update_user(user_id, {"enabled": False})


async def enable_user(user_id: str) -> None:
    await update_user(user_id, {"enabled": True})


async def send_invite(user_id: str) -> None:
    async with await _admin_client() as client:
        resp = await client.put(
            f"users/{user_id}/execute-actions-email",
            json=["UPDATE_PASSWORD"],
        )
        resp.raise_for_status()


async def reset_password_email(user_id: str) -> None:
    await send_invite(user_id)


async def list_realm_roles() -> list[dict]:
    async with await _admin_client() as client:
        resp = await client.get("roles")
        resp.raise_for_status()
        return resp.json()


async def get_user_realm_roles(user_id: str) -> list[dict]:
    async with await _admin_client() as client:
        resp = await client.get(f"users/{user_id}/role-mappings/realm")
        resp.raise_for_status()
        return resp.json()


async def assign_realm_role(user_id: str, role_name: str) -> None:
    role = await _get_realm_role_by_name(role_name)
    async with await _admin_client() as client:
        resp = await client.post(
            f"users/{user_id}/role-mappings/realm",
            json=[role],
        )
        resp.raise_for_status()


async def remove_realm_role(user_id: str, role_name: str) -> None:
    role = await _get_realm_role_by_name(role_name)
    async with await _admin_client() as client:
        resp = await client.request(
            "DELETE",
            f"users/{user_id}/role-mappings/realm",
            json=[role],
        )
        resp.raise_for_status()


async def _get_realm_role_by_name(role_name: str) -> dict:
    async with await _admin_client() as client:
        resp = await client.get(f"roles/{role_name}")
        resp.raise_for_status()
        return resp.json()


async def count_users(search: str = "") -> int:
    async with await _admin_client() as client:
        resp = await client.get("users/count", params={"search": search})
        resp.raise_for_status()
        return resp.json()
