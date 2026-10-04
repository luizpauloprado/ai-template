---
name: http-adapter
description: Use when calling a third-party HTTP API from app/adapters/http/ - httpx client creation, adapter wires for the external payload format, mapping to domain models, and respx tests.
---

# HTTP adapter (third-party APIs)

## Files

| File | Role |
|---|---|
| `app/adapters/http/<api>_client.py` | `create_client(...)` + one `async def` per port |
| `app/adapters/http/<api>_schemas.py` | "Adapter wires": the third party's payload format + `to_<domain>()` |

## Rules

- MUST: adapter functions take `client: httpx.AsyncClient` first, then the port's arguments.
- MUST: use paths relative to the client's `base_url` (`client.get(f"/users/{user_id}")`).
- MUST: validate the response with the adapter wire (`ExternalXWire.model_validate(response.json())`) and return a **domain model** via `to_<domain>(wire)`.
- MUST: treat 404 as "not found" and return `None`. For every other non-2xx status, call `response.raise_for_status()`.
- MUST: adapter wires use `model_config = ConfigDict(extra="ignore")` and `Field(alias="camelCase")` for foreign names.
- MUST NOT: let adapter wires leave the adapter package. Controllers, services and HTTP wires never import them.
- MUST NOT: catch `httpx.HTTPError`. `app/main.py` maps it to 502.
- MUST NOT: create an `httpx.AsyncClient` per call. The client is created once in the lifespan (see `composition`).
- Reuse the existing `app.state.http_client` when the API shares `EXTERNAL_API_BASE_URL`. A different base URL needs a new client, settings and lifespan entries.

## Template: adapter wire (`app/adapters/http/users_api_schemas.py`)

```python
"""Wires da API de usuários: formato que chega pela rede."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import User


class ExternalUserWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    full_name: str = Field(alias="fullName")
    email: str


def to_user(wire: ExternalUserWire) -> User:
    return User(id=wire.id, full_name=wire.full_name, email=wire.email)
```

## Template: client (`app/adapters/http/users_api_client.py`)

```python
"""Adapter HTTP para a API de usuários."""

import httpx

from app.adapters.http.users_api_schemas import ExternalUserWire, to_user
from app.domain.models import User


def create_client(base_url: str, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)


async def fetch_user(client: httpx.AsyncClient, user_id: int) -> User | None:
    response = await client.get(f"/users/{user_id}")
    if response.status_code == httpx.codes.NOT_FOUND:
        return None
    response.raise_for_status()
    return to_user(ExternalUserWire.model_validate(response.json()))
```

For a list endpoint: `[to_user(ExternalUserWire.model_validate(item)) for item in response.json()]`.

## Template: unit test (`tests/unit/test_users_api_client.py`)

```python
import httpx
import pytest
import respx

from app.adapters.http.users_api_client import create_client, fetch_user

BASE_URL = "https://api.test"


@respx.mock
async def test_fetch_user_returns_domain_user() -> None:
    respx.get(f"{BASE_URL}/users/1").respond(
        json={"id": 1, "fullName": "Ana", "email": "a@x.io", "extra": 1}
    )
    async with create_client(BASE_URL, timeout=1) as client:
        user = await fetch_user(client, 1)

    assert user is not None
    assert user.full_name == "Ana"


@respx.mock
async def test_fetch_user_404_returns_none() -> None:
    respx.get(f"{BASE_URL}/users/9").respond(status_code=404)
    async with create_client(BASE_URL, timeout=1) as client:
        assert await fetch_user(client, 9) is None


@respx.mock
async def test_fetch_user_500_raises() -> None:
    respx.get(f"{BASE_URL}/users/1").respond(status_code=500)
    async with create_client(BASE_URL, timeout=1) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_user(client, 1)
```

## Checklist

1. Domain model + port (`FetchUser = Callable[[int], Awaitable[User | None]]`) (see `domain-and-ports`).
2. `<api>_schemas.py` + `<api>_client.py`.
3. If it is a new base URL: add settings, `.env.example`, a lifespan create/close, and a `resources.py` getter + Dep (see `composition`).
4. Provider `get_fetch_user` + `FetchUserDep` (see `composition`).
5. Service, wires and controller (see `services`, `wires-and-controllers`).
6. Tests: respx (above), a fake in `tests/fakes.py`, and acceptance (see `testing`).

## Verify

```bash
make lint && make test-unit && make test-acceptance
```

## Reference implementation

- `app/adapters/http/external_api_client.py`
- `app/adapters/http/external_api_schemas.py`
- `tests/unit/test_external_api_client.py`
