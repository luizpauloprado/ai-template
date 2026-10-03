"""Repository da tabela `item` (Postgres). Funções puras de SQL sobre o pool."""

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from app.domain.models import Item

COLUMNS = "id, details, updated_at"


def to_item(row: dict[str, Any]) -> Item:
    return Item.model_validate(row)


async def insert_item(pool: AsyncConnectionPool, details: dict[str, Any]) -> Item:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"INSERT INTO item (details) VALUES (%s) RETURNING {COLUMNS}", (Jsonb(details),)
        )
        row = await cur.fetchone()
    assert row is not None
    return to_item(row)


async def get_item(pool: AsyncConnectionPool, item_id: int) -> Item | None:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"SELECT {COLUMNS} FROM item WHERE id = %s", (item_id,))
        row = await cur.fetchone()
    return to_item(row) if row else None


async def list_items(pool: AsyncConnectionPool, limit: int, offset: int) -> list[Item]:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT {COLUMNS} FROM item ORDER BY id LIMIT %s OFFSET %s", (limit, offset)
        )
        rows = await cur.fetchall()
    return [to_item(row) for row in rows]


async def update_item(
    pool: AsyncConnectionPool, item_id: int, details: dict[str, Any]
) -> Item | None:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"UPDATE item SET details = %s, updated_at = now() WHERE id = %s RETURNING {COLUMNS}",
            (Jsonb(details), item_id),
        )
        row = await cur.fetchone()
    return to_item(row) if row else None


async def delete_item(pool: AsyncConnectionPool, item_id: int) -> bool:
    async with pool.connection() as conn:
        cursor = await conn.execute("DELETE FROM item WHERE id = %s", (item_id,))
    return cursor.rowcount > 0
