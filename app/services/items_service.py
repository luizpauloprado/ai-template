from typing import Any

from app.domain.models import Item
from app.domain.ports import DeleteItem, GetItem, InsertItem, ListItems, UpdateItem


async def create_item(details: dict[str, Any], insert_item: InsertItem) -> Item:
    return await insert_item(details)


async def get_item(item_id: int, get: GetItem) -> Item | None:
    return await get(item_id)


async def list_items(limit: int, offset: int, list_all: ListItems) -> list[Item]:
    return await list_all(limit, offset)


async def update_item(item_id: int, details: dict[str, Any], update: UpdateItem) -> Item | None:
    return await update(item_id, details)


async def delete_item(item_id: int, delete: DeleteItem) -> bool:
    return await delete(item_id)
