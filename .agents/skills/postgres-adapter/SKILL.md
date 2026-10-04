---
name: postgres-adapter
description: Use when writing SQL or a repository in app/adapters/db/, adding a table in db/init/, adding a Postgres health check, or working with pgvector/pgmq.
---

# Postgres adapter (repositories, SQL, health checks)

## Files

| File | Role |
|---|---|
| `db/init/NN-<name>.sql` | Schema. Runs once, on an **empty** volume, in filename order |
| `app/adapters/db/postgres_adapter.py` | Pool lifecycle (`create_pool`, `close_pool`) + health checks |
| `app/adapters/db/<entity>_repository.py` | SQL for one table. One `async def` per port |
| `docker/postgres.Dockerfile` | Postgres 17 + pgvector + PGMQ (built from source) |

## Rules

- MUST: the first parameter is `pool: AsyncConnectionPool`, followed by exactly the port's arguments in the same order.
- MUST: use `async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:` and convert rows with `to_<entity>(row)` → `<Entity>.model_validate(row)`.
- MUST: **always** pass values as `%s` parameters. The only f-string interpolation allowed is the module constant `COLUMNS`.
- MUST: wrap dict/list values bound for `JSONB` columns in `Jsonb(...)` (`from psycopg.types.json import Jsonb`).
- MUST: use `RETURNING {COLUMNS}` on INSERT/UPDATE so the function returns the fresh entity without a second query.
- MUST: return `None` when `fetchone()` yields nothing on get/update, and `cursor.rowcount > 0` on delete.
- MUST: set `updated_at = now()` explicitly in UPDATE statements. There are no triggers.
- MUST: list queries use `ORDER BY id LIMIT %s OFFSET %s`.
- MUST NOT: return rows, tuples or dicts. Return domain models only.
- MUST NOT: open transactions manually for single statements. The pool connection context commits on exit.
- New SQL files are numbered sequentially (`03-...`) and use `IF NOT EXISTS`.

## Template: schema (`db/init/03-note.sql`)

```sql
CREATE TABLE IF NOT EXISTS note (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title      TEXT NOT NULL,
    details    JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Apply it with `make reset`, which **wipes the local DB**. Alternatively, paste it into `docker compose exec db psql -U app -d app` to keep existing data.

## Template: repository (`app/adapters/db/note_repository.py`)

```python
"""Repository da tabela `note` (Postgres). Funções puras de SQL sobre o pool."""

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from app.domain.models import Note

COLUMNS = "id, title, details, updated_at"


def to_note(row: dict[str, Any]) -> Note:
    return Note.model_validate(row)


async def insert_note(pool: AsyncConnectionPool, title: str, details: dict[str, Any]) -> Note:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"INSERT INTO note (title, details) VALUES (%s, %s) RETURNING {COLUMNS}",
            (title, Jsonb(details)),
        )
        row = await cur.fetchone()
    assert row is not None
    return to_note(row)


async def get_note(pool: AsyncConnectionPool, note_id: int) -> Note | None:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"SELECT {COLUMNS} FROM note WHERE id = %s", (note_id,))
        row = await cur.fetchone()
    return to_note(row) if row else None


async def list_notes(pool: AsyncConnectionPool, limit: int, offset: int) -> list[Note]:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT {COLUMNS} FROM note ORDER BY id LIMIT %s OFFSET %s", (limit, offset)
        )
        rows = await cur.fetchall()
    return [to_note(row) for row in rows]


async def update_note(
    pool: AsyncConnectionPool, note_id: int, title: str, details: dict[str, Any]
) -> Note | None:
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "UPDATE note SET title = %s, details = %s, updated_at = now() "
            f"WHERE id = %s RETURNING {COLUMNS}",
            (title, Jsonb(details), note_id),
        )
        row = await cur.fetchone()
    return to_note(row) if row else None


async def delete_note(pool: AsyncConnectionPool, note_id: int) -> bool:
    async with pool.connection() as conn:
        cursor = await conn.execute("DELETE FROM note WHERE id = %s", (note_id,))
    return cursor.rowcount > 0
```

## Template: health check

1. In `app/adapters/db/postgres_adapter.py`, add a check that returns `ComponentStatus`. It may raise, because `health_service.run_check` turns exceptions and timeouts into `down`.

```python
async def check_note_table(pool: AsyncConnectionPool) -> ComponentStatus:
    async with pool.connection() as conn:
        cursor = await conn.execute("SELECT count(*) FROM note")
        row = await cursor.fetchone()
    return ComponentStatus(status="up", detail=f"{row[0] if row else 0} row(s)")
```

2. Register it in `get_health_checks` in `app/dependencies/ports/health.py`: `"note_table": partial(postgres_adapter.check_note_table, pool)`.

## pgvector and PGMQ

- Both extensions and the `default` queue are created in `db/init/01-extensions.sql`.
- pgvector: declare columns as `embedding vector(<dims>)` in SQL. Pass vectors as a string literal `'[0.1,0.2,...]'` cast with `%s::vector`, or register the adapter from the `pgvector` package (not installed yet; add it to `requirements.txt` first).
- PGMQ: use its SQL API through the same pool (`SELECT pgmq.send(%s, %s)`, `SELECT * FROM pgmq.read(%s, %s, %s)`). Put queue operations in their own adapter module (e.g. `app/adapters/db/queue_adapter.py`) behind ports, never in a service.

## Checklist

1. `db/init/NN-<entity>.sql`, then `make reset` (or apply it manually).
2. `app/adapters/db/<entity>_repository.py`, with one function per port and signatures matching the port after `pool`.
3. Provider + `*Dep` (see `composition`).
4. `tests/integration/test_<entity>_repository.py` (see `testing`).
5. Update the "Banco de dados" section of `README.md`.

## Verify

```bash
make db && make lint && make test-integration
```

## Reference implementation

- `db/init/02-item.sql`
- `app/adapters/db/item_repository.py`
- `app/adapters/db/postgres_adapter.py`: pool and `check_*` functions
- `tests/integration/test_item_repository.py`
