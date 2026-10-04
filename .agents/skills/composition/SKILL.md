---
name: composition
description: Use when binding ports to adapters (app/dependencies/), adding a *Dep alias, adding a new long-lived resource (pool/client) to app/lifespan.py and app.state, or adding a setting to app/config.py.
---

# Composition (dependencies, lifespan, settings)

This is the **only** place where ports meet adapters.

## Files

| File | Role |
|---|---|
| `app/config.py` | `Settings` (pydantic-settings, reads `.env`) + `get_settings()` (`lru_cache`) |
| `app/lifespan.py` | Creates resources at startup, stores them in `app.state`, closes them at shutdown |
| `app/dependencies/settings.py` | `SettingsDep` |
| `app/dependencies/resources.py` | `get_<resource>(request)` reads `request.app.state.<resource>`, plus `<Resource>Dep` aliases |
| `app/dependencies/ports/<feature>.py` | Providers: `get_<port_snake>(...) -> Port` + `<Port>Dep` aliases |
| `app/dependencies/__init__.py` | Re-exports every provider and alias, listed in `__all__` |

## Rules

- MUST: a provider returns `partial(adapter_fn, <resources...>)`, and its return type is the port alias.
- MUST: every provider has a sibling alias `<Port>Dep = Annotated[<Port>, Depends(get_<port_snake>)]`.
- MUST: providers receive resources via `PoolDep`, `GeminiClientDep`, `HttpClientDep` and `SettingsDep`, never by touching `app.state` directly.
- MUST: re-export both `get_*` (tests override these) and `*Dep` (controllers use these) in `app/dependencies/__init__.py` and add them to `__all__` (kept sorted).
- MUST: a resource created in the lifespan is closed in its `finally:` block, when it has a close method.
- MUST NOT: create clients or pools per request inside providers.
- MUST NOT: read `os.environ`. Add a field to `Settings` instead.

## Naming

| Port alias | Provider | Dep alias |
|---|---|---|
| `GetNote` | `get_get_note` | `GetNoteDep` |
| `InsertNote` | `get_insert_note` | `InsertNoteDep` |
| `FetchPost` | `get_fetch_post` | `FetchPostDep` |
| `dict[str, CheckComponent]` | `get_health_checks` | `HealthChecksDep` |

## Template: provider (`app/dependencies/ports/note.py`)

```python
from functools import partial
from typing import Annotated

from fastapi import Depends

from app.adapters.db import note_repository
from app.dependencies.resources import PoolDep
from app.domain.ports import DeleteNote, GetNote, InsertNote, ListNotes, UpdateNote


def get_insert_note(pool: PoolDep) -> InsertNote:
    return partial(note_repository.insert_note, pool)


def get_get_note(pool: PoolDep) -> GetNote:
    return partial(note_repository.get_note, pool)


def get_list_notes(pool: PoolDep) -> ListNotes:
    return partial(note_repository.list_notes, pool)


def get_update_note(pool: PoolDep) -> UpdateNote:
    return partial(note_repository.update_note, pool)


def get_delete_note(pool: PoolDep) -> DeleteNote:
    return partial(note_repository.delete_note, pool)


InsertNoteDep = Annotated[InsertNote, Depends(get_insert_note)]
GetNoteDep = Annotated[GetNote, Depends(get_get_note)]
ListNotesDep = Annotated[ListNotes, Depends(get_list_notes)]
UpdateNoteDep = Annotated[UpdateNote, Depends(get_update_note)]
DeleteNoteDep = Annotated[DeleteNote, Depends(get_delete_note)]
```

When the adapter needs more than one bound value (e.g. a client and a model name from settings), bind them in order:

```python
def get_ask(client: GeminiClientDep, settings: SettingsDep) -> Ask:
    return partial(gemini_adapter.ask, client, settings.gemini_model)
```

## Template: re-export (`app/dependencies/__init__.py`)

```python
from app.dependencies.ports.note import (
    DeleteNoteDep,
    GetNoteDep,
    InsertNoteDep,
    ListNotesDep,
    UpdateNoteDep,
    get_delete_note,
    get_get_note,
    get_insert_note,
    get_list_notes,
    get_update_note,
)

__all__ = [
    # ...existing names, keep alphabetical...
    "DeleteNoteDep",
    "GetNoteDep",
    "InsertNoteDep",
    "ListNotesDep",
    "UpdateNoteDep",
    "get_delete_note",
    "get_get_note",
    "get_insert_note",
    "get_list_notes",
    "get_update_note",
]
```

## Template: new resource (e.g. a second HTTP client)

1. `app/config.py`: add the settings fields with defaults (`users_api_base_url: str = "https://..."`).
2. `.env.example`: add `USERS_API_BASE_URL=...`. Add it to the variables table in `README.md` too.
3. The adapter (`app/adapters/http/users_api_client.py`) exposes `create_client(...)` (see `http-adapter`).
4. `app/lifespan.py`:

```python
    app.state.users_client = users_api_client.create_client(
        settings.users_api_base_url, settings.http_timeout_seconds
    )
    try:
        yield
    finally:
        await app.state.users_client.aclose()
        ...existing closes...
```

5. `app/dependencies/resources.py`:

```python
def get_users_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.users_client


UsersClientDep = Annotated[httpx.AsyncClient, Depends(get_users_client)]
```

6. Re-export `get_users_client` / `UsersClientDep` in `app/dependencies/__init__.py`.

### Optional resource (may be missing)

Follow `get_gemini_client`. Store `None` in `app.state` when it is not configured, and raise `HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "<SETTING> não configurada")` in the getter.

## Checklist

1. Provider + `*Dep` in `app/dependencies/ports/<feature>.py`.
2. Re-export in `app/dependencies/__init__.py` and `__all__`.
3. For a new resource: settings, `.env.example`, lifespan create/close, `resources.py` getter + Dep.
4. Add `dependency_overrides` for the new `get_*` providers in `tests/acceptance/conftest.py` (see `testing`).

## Verify

```bash
make lint && make test-acceptance
```

## Reference implementation

- `app/dependencies/ports/ai.py`: canonical `*Dep` pattern, partial with two bound values
- `app/dependencies/ports/items.py`: one provider per repository function
- `app/dependencies/ports/health.py`: provider returning a dict of ports
- `app/dependencies/resources.py`: resource getters, optional resource → 503
- `app/lifespan.py`: resource lifecycle
