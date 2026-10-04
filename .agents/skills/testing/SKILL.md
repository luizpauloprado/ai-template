---
name: testing
description: Use when writing tests - fakes for ports in tests/fakes.py, unit tests for services/adapters/wires, acceptance tests for endpoints with dependency_overrides, and integration tests against real Postgres.
---

# Testing

## Layout

| Folder | What | I/O | Command |
|---|---|---|---|
| `tests/unit/` | Services (with fakes), wires, adapters (`respx` / `AsyncMock`) | None | `make test-unit` |
| `tests/acceptance/` | Endpoints via ASGI, ports replaced with fakes | None | `make test-acceptance` |
| `tests/integration/` | Repositories and endpoints against real Postgres | Postgres | `make db && make test-integration` |
| `tests/fakes.py` | Fake implementations of every port | — | — |

## Rules

- MUST: tests are plain `async def test_<behavior>() -> None:` functions. No `@pytest.mark.asyncio` (`asyncio_mode = "auto"`) and no test classes.
- MUST: fakes are **functions built by factories** in `tests/fakes.py` and typed with the port alias. Do not use `MagicMock` for ports.
- MUST: acceptance tests override providers (`get_*` from `app.dependencies`), never `*Dep` aliases and never adapters.
- MUST: integration test modules set `pytestmark = pytest.mark.integration`, create their own data, and delete it in `try/finally`.
- MUST: every new endpoint has acceptance tests for success, 404 (if applicable) and 422 (invalid input).
- Arrange / act / assert separated by blank lines. One behavior per test.
- Use `unittest.mock.AsyncMock` only for third-party SDK clients (Gemini) and `respx` for httpx.

## How the acceptance app works

`tests/acceptance/conftest.py` builds `create_app()` **without running the lifespan**, so `app.state` has no pool or clients. It provides these fixtures:

- `item_table`: the fake table from `make_fake_item_table()`
- `app`: `create_app()` with the item ports overridden globally
- `client`: `httpx.AsyncClient(transport=ASGITransport(app=app))`

Any route whose providers are not overridden fails (e.g. Gemini returns 503 because `gemini_client` is missing).

## Template: fake for a DB entity (`tests/fakes.py`)

```python
def make_fake_note_table() -> dict[str, Any]:
    """Simula a tabela `note` com um dict. Retorna as funções que implementam os ports."""
    rows: dict[int, Note] = {}
    ids = count(1)

    async def insert(title: str, details: dict[str, Any]) -> Note:
        note = Note(id=next(ids), title=title, details=details, updated_at=datetime.now(UTC))
        rows[note.id] = note
        return note

    async def get(note_id: int) -> Note | None:
        return rows.get(note_id)

    async def list_all(limit: int, offset: int) -> list[Note]:
        return [rows[key] for key in sorted(rows)][offset : offset + limit]

    async def update(note_id: int, title: str, details: dict[str, Any]) -> Note | None:
        if note_id not in rows:
            return None
        rows[note_id] = Note(id=note_id, title=title, details=details, updated_at=datetime.now(UTC))
        return rows[note_id]

    async def delete(note_id: int) -> bool:
        return rows.pop(note_id, None) is not None

    return {"insert": insert, "get": get, "list": list_all, "update": update, "delete": delete}
```

## Template: fake for a single port

```python
def fake_fetch_user(users: dict[int, User]) -> FetchUser:
    async def fetch_user(user_id: int) -> User | None:
        return users.get(user_id)

    return fetch_user
```

To assert what reached the port, accept an optional `calls: list[...]` and append to it (see `fake_ask_with_config`).

## Template: service unit test (`tests/unit/test_note_service.py`)

```python
from app.services import note_service
from tests.fakes import make_fake_note_table


async def test_create_and_get() -> None:
    table = make_fake_note_table()

    created = await note_service.create_note(" a ", {}, table["insert"])
    found = await note_service.get_note(created.id, table["get"])

    assert found == created
    assert created.title == "a"


async def test_update_missing_returns_none() -> None:
    table = make_fake_note_table()

    assert await note_service.update_note(99, "x", {}, table["update"]) is None
```

## Template: acceptance tests

**Option 1 (CRUD entity, used by many tests):** add a fixture and global overrides in `tests/acceptance/conftest.py`:

```python
@pytest.fixture
def note_table() -> dict[str, Any]:
    return make_fake_note_table()

# inside the `app` fixture (add `note_table` to its parameters):
    app.dependency_overrides.update(
        {
            deps.get_insert_note: lambda: note_table["insert"],
            deps.get_get_note: lambda: note_table["get"],
            deps.get_list_notes: lambda: note_table["list"],
            deps.get_update_note: lambda: note_table["update"],
            deps.get_delete_note: lambda: note_table["delete"],
        }
    )
```

**Option 2 (single port):** override inside the test:

```python
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies import get_fetch_user
from app.domain.models import User
from tests.fakes import fake_fetch_user


async def test_get_user(app: FastAPI, client: AsyncClient) -> None:
    user = User(id=1, full_name="Ana", email="a@x.io")
    app.dependency_overrides[get_fetch_user] = lambda: fake_fetch_user({1: user})

    response = await client.get("/users/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "full_name": "Ana", "email": "a@x.io"}


async def test_get_user_not_found(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_fetch_user] = lambda: fake_fetch_user({})

    assert (await client.get("/users/9")).status_code == 404
```

To test the 502 mapping, override the provider with a function that raises `httpx.ConnectError("down")` (see `test_upstream_error_returns_502`).

## Template: integration test (`tests/integration/test_note_repository.py`)

```python
import pytest
from psycopg_pool import AsyncConnectionPool

from app.adapters.db import note_repository as repo

pytestmark = pytest.mark.integration


async def test_note_repository_roundtrip(pool: AsyncConnectionPool) -> None:
    created = await repo.insert_note(pool, "integration", {"tags": ["a"]})
    try:
        assert (await repo.get_note(pool, created.id)) == created

        updated = await repo.update_note(pool, created.id, "changed", {})
        assert updated is not None
        assert updated.title == "changed"
        assert updated.updated_at > created.updated_at
    finally:
        assert await repo.delete_note(pool, created.id) is True

    assert await repo.get_note(pool, created.id) is None
```

The `pool` fixture (in `tests/integration/conftest.py`) skips the test when Postgres is down. The `client` fixture there injects the real pool into `app.state.db_pool` for endpoint tests.

## Checklist for a new feature

1. Fake(s) in `tests/fakes.py`.
2. `tests/unit/test_<feature>_service.py`.
3. Adapter unit test if it calls HTTP/SDK (`respx` / `AsyncMock`).
4. Inbound wire validation test in `tests/unit/test_wires.py` when constraints are non-trivial.
5. `tests/acceptance/test_<feature>_endpoint.py`: success, 404, 422.
6. `tests/integration/test_<entity>_repository.py` for every new SQL function.

## Verify

```bash
make lint && make test   # run `make db` first so integration tests are not skipped
```

## Reference implementation

- `tests/fakes.py`
- `tests/acceptance/conftest.py`, `tests/acceptance/test_items_endpoint.py`, `tests/acceptance/test_ai_endpoint.py`, `tests/acceptance/test_external_endpoint.py`
- `tests/unit/test_items_service.py`, `tests/unit/test_health_service.py`, `tests/unit/test_gemini_adapter.py`, `tests/unit/test_external_api_client.py`
- `tests/integration/conftest.py`, `tests/integration/test_item_repository.py`
