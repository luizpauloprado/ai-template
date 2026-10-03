from datetime import datetime

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_health_with_real_database(client: AsyncClient) -> None:
    response = await client.get("/health")

    body = response.json()
    assert response.status_code == 200, body
    for name in ("database", "pgvector", "pgmq"):
        assert body["components"][name]["status"] == "up"
        assert body["components"][name]["version"]


async def test_items_crud_with_real_database(client: AsyncClient) -> None:
    created = (await client.post("/items", json={"details": {"source": "test"}})).json()

    fetched = await client.get(f"/items/{created['id']}")
    assert fetched.json() == created

    updated = await client.put(f"/items/{created['id']}", json={"details": {"source": "put"}})
    assert datetime.fromisoformat(updated.json()["updated_at"]) > datetime.fromisoformat(
        created["updated_at"]
    )

    assert (await client.delete(f"/items/{created['id']}")).status_code == 204
