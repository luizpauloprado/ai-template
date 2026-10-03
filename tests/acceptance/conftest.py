from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import dependencies as deps
from app.main import create_app
from tests.fakes import make_fake_item_table


@pytest.fixture
def item_table() -> dict[str, Any]:
    return make_fake_item_table()


@pytest.fixture
def app(item_table: dict[str, Any]) -> FastAPI:
    """App sem lifespan (sem banco/rede): os ports de item usam a tabela fake."""
    app = create_app()
    app.dependency_overrides.update(
        {
            deps.get_insert_item: lambda: item_table["insert"],
            deps.get_get_item: lambda: item_table["get"],
            deps.get_list_items: lambda: item_table["list"],
            deps.get_update_item: lambda: item_table["update"],
            deps.get_delete_item: lambda: item_table["delete"],
        }
    )
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
