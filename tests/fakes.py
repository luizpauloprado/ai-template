"""Fakes dos ports: funções simples, sem banco nem rede."""

from datetime import UTC, datetime
from itertools import count
from typing import Any

from app.domain.models import ComponentStatus, GeneratedText, Item, Post
from app.domain.ports import CheckComponent, FetchPost, GenerateText


def make_fake_item_table() -> dict[str, Any]:
    """Simula a tabela `item` com um dict. Retorna as funções que implementam os ports."""
    rows: dict[int, Item] = {}
    ids = count(1)

    async def insert(details: dict[str, Any]) -> Item:
        item = Item(id=next(ids), details=details, updated_at=datetime.now(UTC))
        rows[item.id] = item
        return item

    async def get(item_id: int) -> Item | None:
        return rows.get(item_id)

    async def list_all(limit: int, offset: int) -> list[Item]:
        return [rows[key] for key in sorted(rows)][offset : offset + limit]

    async def update(item_id: int, details: dict[str, Any]) -> Item | None:
        if item_id not in rows:
            return None
        rows[item_id] = Item(id=item_id, details=details, updated_at=datetime.now(UTC))
        return rows[item_id]

    async def delete(item_id: int) -> bool:
        return rows.pop(item_id, None) is not None

    return {"insert": insert, "get": get, "list": list_all, "update": update, "delete": delete}


def fake_check(status: ComponentStatus) -> CheckComponent:
    async def check() -> ComponentStatus:
        return status

    return check


def failing_check(exc: Exception) -> CheckComponent:
    async def check() -> ComponentStatus:
        raise exc

    return check


def fake_generate_text(model: str = "fake-model") -> GenerateText:
    async def generate_text(prompt: str) -> GeneratedText:
        return GeneratedText(text=f"echo: {prompt}", model=model)

    return generate_text


def fake_fetch_post(posts: dict[int, Post]) -> FetchPost:
    async def fetch_post(post_id: int) -> Post | None:
        return posts.get(post_id)

    return fetch_post
