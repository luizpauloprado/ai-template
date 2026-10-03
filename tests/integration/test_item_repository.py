import pytest
from psycopg_pool import AsyncConnectionPool

from app.adapters.db import item_repository as repo

pytestmark = pytest.mark.integration


async def test_item_repository_roundtrip(pool: AsyncConnectionPool) -> None:
    created = await repo.insert_item(pool, {"name": "integration", "tags": ["a"]})
    try:
        assert (await repo.get_item(pool, created.id)) == created

        updated = await repo.update_item(pool, created.id, {"name": "changed"})
        assert updated is not None
        assert updated.details == {"name": "changed"}
        assert updated.updated_at > created.updated_at

        listed = await repo.list_items(pool, limit=100, offset=0)
        assert created.id in [item.id for item in listed]
    finally:
        assert await repo.delete_item(pool, created.id) is True

    assert await repo.get_item(pool, created.id) is None
    assert await repo.delete_item(pool, created.id) is False
