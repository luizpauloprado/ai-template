"""Testes contra o Postgres real. Rode `make db` antes; sem banco, são pulados."""

from collections.abc import AsyncIterator

import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import AsyncConnectionPool

from app.adapters.db.postgres_adapter import close_pool, create_pool
from app.config import get_settings
from app.main import create_app


@pytest.fixture
async def pool() -> AsyncIterator[AsyncConnectionPool]:
    database_url = get_settings().database_url
    try:
        conn = await psycopg.AsyncConnection.connect(database_url, connect_timeout=2)
        await conn.close()
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres indisponível ({exc.__class__.__name__}); rode `make db`")

    pool = await create_pool(database_url)
    await pool.wait()
    yield pool
    await close_pool(pool)


@pytest.fixture
async def client(pool: AsyncConnectionPool) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app()
    app.state.db_pool = pool
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
