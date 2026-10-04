---
name: services
description: Use when writing or changing business logic in app/services/. Services are plain async functions that receive ports as parameters and never touch infrastructure.
---

# Services

## Files

- `app/services/<feature>_service.py`, one module per feature (`items_service.py`, `ai_service.py`, ...)

## Rules

- MUST: be module-level `async def` functions. No classes.
- MUST: take data arguments first and **ports last**, each typed with its alias from `app.domain.ports`.
- MUST: return domain models (or `None` / `bool` / `list[...]`, mirroring the port).
- MUST: import only from `app.domain` (plus the stdlib).
- MUST NOT: import fastapi, `HTTPException`, httpx, psycopg, google.genai, adapters, wires, dependencies or config.
- MUST NOT: raise HTTP errors. Return `None` / `False`; the controller maps them to 404.
- MUST NOT: catch infrastructure exceptions. Let them reach the handlers in `app/main.py` (502).
- Business rules (normalization, validation beyond the schema, orchestration of several ports, timeouts) belong here.
- Name the port parameter after its role (`get`, `insert_item`, `llm`, `fetch_post`). Keep the names stable across functions.

## Template (`app/services/note_service.py`)

```python
from typing import Any

from app.domain.models import Note
from app.domain.ports import DeleteNote, GetNote, InsertNote, ListNotes, UpdateNote


async def create_note(title: str, details: dict[str, Any], insert: InsertNote) -> Note:
    return await insert(title.strip(), details)


async def get_note(note_id: int, get: GetNote) -> Note | None:
    return await get(note_id)


async def list_notes(limit: int, offset: int, list_all: ListNotes) -> list[Note]:
    return await list_all(limit, offset)


async def update_note(
    note_id: int, title: str, details: dict[str, Any], update: UpdateNote
) -> Note | None:
    return await update(note_id, title.strip(), details)


async def delete_note(note_id: int, delete: DeleteNote) -> bool:
    return await delete(note_id)
```

### Several ports in one use case

When a use case needs more than one port, pass each as its own parameter. Use `Mapping[str, Port]` when the set is dynamic, as `health_service.get_health` does.

```python
async def summarize_note(note_id: int, get: GetNote, llm: Ask) -> GeneratedText | None:
    note = await get(note_id)
    if note is None:
        return None
    return await llm(f"Summarize: {note.title}\n{note.details}")
```

## Checklist

1. Create `app/services/<feature>_service.py` with one function per use case.
2. Add `tests/unit/test_<feature>_service.py` using fakes from `tests/fakes.py` (see `testing`).

## Verify

```bash
make lint && make test-unit
```

## Reference implementation

- `app/services/items_service.py`: CRUD pass-through
- `app/services/ai_service.py`: input normalization (`prompt.strip()`)
- `app/services/health_service.py`: real logic (parallel checks, timeouts, aggregation)
