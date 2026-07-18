from __future__ import annotations

import logging
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=True)
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.keycloak_jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


class TokenUser:
    def __init__(self, payload: dict) -> None:
        self.sub: str = payload["sub"]
        self.email: str = payload.get("email", "")
        self.name: str = payload.get("name", "")
        self.realm_roles: list[str] = payload.get("realm_access", {}).get("roles", [])
        self._payload = payload

    @property
    def is_admin(self) -> bool:
        return settings.admin_role in self.realm_roles


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> TokenUser:
    token = creds.credentials
    try:
        await _get_jwks()
        signing_key = jwt.PyJWKClient(settings.keycloak_jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_aud": False},
            issuer=settings.keycloak_issuer,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.PyJWTError as exc:
        logger.debug("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    user = TokenUser(payload)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{settings.admin_role}' required",
        )
    return user


CurrentUser = Annotated[TokenUser, Depends(get_current_user)]
