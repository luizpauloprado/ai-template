---
name: domain-and-ports
description: Use when adding or changing domain models (app/domain/models.py) or port signatures (app/domain/ports.py). Covers immutable Pydantic entities and ports as Callable type aliases.
---

# Domain models and ports

## Files

- `app/domain/models.py`: entities and value objects
- `app/domain/ports.py`: contracts the services depend on

## Rules

- MUST: models extend `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True)`.
- MUST: ports are **type aliases** of `Callable[[args...], Awaitable[Result]]`. They are not Protocols, ABCs or classes.
- MUST: import `Callable`/`Awaitable` from `collections.abc`.
- MUST NOT: import fastapi, httpx, psycopg, google.genai, or anything from `app.adapters`, `app.wires`, `app.dependencies` or `app.services`.
- MUST NOT: put HTTP concerns (status codes, aliases like `userId`) or DB concerns (SQL, `Jsonb`) in domain models.
- Use `Literal[...]` aliases for small enums (see `ComponentState`).
- Optional fields default to `None`.

## Return type conventions for ports

| Operation | Return type | Meaning |
|---|---|---|
| Create | `Awaitable[Note]` | Always returns the created entity |
| Get by id / fetch one | `Awaitable[Note \| None]` | `None` means "not found" (the controller turns it into 404) |
| List | `Awaitable[list[Note]]` | Empty list when nothing matches |
| Update | `Awaitable[Note \| None]` | `None` means "not found" |
| Delete | `Awaitable[bool]` | `False` means "not found" |
| Health check | `Awaitable[ComponentStatus]` | See `CheckComponent` |

## Template: model (`app/domain/models.py`)

```python
class Note(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    title: str
    details: dict[str, Any]
    updated_at: datetime
```

## Template: ports (`app/domain/ports.py`)

Add the model to the existing `from app.domain.models import ...` line, then append a new group:

```python
# Repository de Note
InsertNote = Callable[[str, dict[str, Any]], Awaitable[Note]]  # (title, details)
GetNote = Callable[[int], Awaitable[Note | None]]
ListNotes = Callable[[int, int], Awaitable[list[Note]]]  # (limit, offset)
UpdateNote = Callable[[int, str, dict[str, Any]], Awaitable[Note | None]]  # (id, title, details)
DeleteNote = Callable[[int], Awaitable[bool]]
```

Add a `# (a, b)` comment whenever two or more positional arguments share a type.

## Checklist

1. Add the model to `app/domain/models.py`.
2. Add the ports to `app/domain/ports.py` and update its import line.
3. Every port you add needs: an adapter function (see `postgres-adapter`, `http-adapter` or `ai-adapter`), a provider + `*Dep` (see `composition`), and a fake (see `testing`).

## Verify

```bash
make lint
```

## Reference implementation

- `app/domain/models.py`: `Item`, `Post`, `GeneratedText`, `GenerationConfig`, `HealthStatus`
- `app/domain/ports.py`: all current ports
