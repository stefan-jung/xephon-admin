from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import TokenUser, get_current_user
from app.db.session import engine, get_db
from app.main import app


def _admin_user() -> TokenUser:
    return TokenUser(
        {
            "sub": "test-admin-sub",
            "email": "admin@test.example",
            "name": "Test Admin",
            "realm_access": {"roles": ["xephon:admin"]},
        }
    )


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        await connection.begin()
        async with AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            yield session
        await connection.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _get_db_override() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _get_current_user_override() -> TokenUser:
        return _admin_user()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac
    app.dependency_overrides.clear()
