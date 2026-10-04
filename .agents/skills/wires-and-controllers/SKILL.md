---
name: wires-and-controllers
description: Use when adding or changing HTTP request/response contracts (app/wires/) or FastAPI routes (app/controllers/), including registering a router in app/main.py and mapping not-found to 404.
---

# Wires (HTTP contracts) and controllers

## Files

- `app/wires/inbound/<feature>.py`: request bodies (`XIn`) + `to_<domain>(wire_in)` when the body maps to a domain model
- `app/wires/outbound/<feature>.py`: responses (`XOut`) + `to_<x>_out(domain)`
- `app/controllers/<feature>_controller.py`: routes
- `app/main.py`: router registration

## Rules: wires

- MUST: wires are Pydantic `BaseModel`s, **not** frozen. They are the public API contract.
- MUST: put input validation in the inbound wire with `Field(...)` (`min_length`, `max_length`, `ge`, `le`).
- MUST: every outbound wire has a `to_<x>_out(domain) -> XOut` function in the same file. Build it field by field, or with `XOut(**domain.model_dump())` when the shapes are identical.
- MUST: import only from `app.domain` (plus pydantic/stdlib).
- MUST NOT: reuse a domain model as a request or response. Always declare `XIn` / `XOut`.
- MUST NOT: put third-party API formats here. Those go in `app/adapters/http/<api>_schemas.py` (see `http-adapter`).

## Rules: controllers

- MUST: `router = APIRouter(prefix="/<plural>", tags=["<plural>"])` at module level.
- MUST: each route is `async def`, declares `response_model=`, and returns `to_<x>_out(...)`.
- MUST: inject ports **only** via `*Dep` aliases imported from `app.dependencies` (e.g. `insert: InsertNoteDep`).
- MUST: call a function from `app.services.<feature>_service`, never the port directly and never an adapter.
- MUST: map `None` to 404 with `ensure_found` (or `HTTPException(status.HTTP_404_NOT_FOUND, "<entity> not found")`).
- Status codes: create uses `status_code=status.HTTP_201_CREATED`. Delete uses `status_code=status.HTTP_204_NO_CONTENT` and returns `Response(status_code=status.HTTP_204_NO_CONTENT)`.
- Path ids use `Annotated[int, Path(ge=1)]`. Pagination uses `limit: Annotated[int, Query(ge=1, le=100)] = 20` and `offset: Annotated[int, Query(ge=0)] = 0`.
- MUST NOT: contain business logic, SQL, try/except around infrastructure errors, or `app.state` access.

## Template: inbound wire (`app/wires/inbound/note.py`)

```python
from typing import Any

from pydantic import BaseModel, Field


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    details: dict[str, Any] = Field(default_factory=dict)
```

If the body maps to a domain value object (like `AskWithConfigIn` maps to `GenerationConfig`), add a converter in the same file:

```python
def to_generation_config(wire_in: AskWithConfigIn) -> GenerationConfig:
    return GenerationConfig(**wire_in.model_dump(exclude={"prompt"}))
```

## Template: outbound wire (`app/wires/outbound/note.py`)

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.models import Note


class NoteOut(BaseModel):
    id: int
    title: str
    details: dict[str, Any]
    updated_at: datetime


def to_note_out(note: Note) -> NoteOut:
    return NoteOut(id=note.id, title=note.title, details=note.details, updated_at=note.updated_at)
```

## Template: controller (`app/controllers/note_controller.py`)

```python
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from app.dependencies import (
    DeleteNoteDep,
    GetNoteDep,
    InsertNoteDep,
    ListNotesDep,
    UpdateNoteDep,
)
from app.domain.models import Note
from app.services import note_service
from app.wires.inbound.note import NoteIn
from app.wires.outbound.note import NoteOut, to_note_out

router = APIRouter(prefix="/notes", tags=["notes"])

NoteId = Annotated[int, Path(ge=1)]


def ensure_found(note: Note | None) -> Note:
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return note


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(wire_in: NoteIn, insert: InsertNoteDep) -> NoteOut:
    note = await note_service.create_note(wire_in.title, wire_in.details, insert)
    return to_note_out(note)


@router.get("", response_model=list[NoteOut])
async def list_notes(
    list_all: ListNotesDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NoteOut]:
    notes = await note_service.list_notes(limit, offset, list_all)
    return [to_note_out(note) for note in notes]


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: NoteId, get: GetNoteDep) -> NoteOut:
    note = await note_service.get_note(note_id, get)
    return to_note_out(ensure_found(note))


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(note_id: NoteId, wire_in: NoteIn, update: UpdateNoteDep) -> NoteOut:
    note = await note_service.update_note(note_id, wire_in.title, wire_in.details, update)
    return to_note_out(ensure_found(note))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: NoteId, delete: DeleteNoteDep) -> Response:
    if not await note_service.delete_note(note_id, delete):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

Parameters without defaults (path, body, `*Dep`) must come before parameters with defaults (`Query(...) = 20`).

## Template: register the router (`app/main.py`)

```python
from app.controllers import (
    ai_controller,
    external_controller,
    health_controller,
    items_controller,
    note_controller,
)
...
    app.include_router(note_controller.router)
```

Keep the import sorted (ruff `I`). Lines may not exceed 100 characters.

## Checklist

1. Create the inbound wire (only if the route has a body).
2. Create the outbound wire with `to_<x>_out`.
3. Make sure the `*Dep` aliases exist and are re-exported in `app/dependencies/__init__.py` (see `composition`).
4. Create the controller.
5. Register the router in `create_app()` in `app/main.py`.
6. Add acceptance tests for success, 404 and 422 (see `testing`).
7. Update the endpoints table in `README.md` and `AGENTS.md`.

## Verify

```bash
make lint && make test-unit && make test-acceptance
```

## Reference implementation

- `app/controllers/items_controller.py`: full CRUD, `ensure_found`, pagination
- `app/controllers/ai_controller.py`: `*Dep` aliases, inbound→domain converter
- `app/controllers/health_controller.py`: dynamic status code via `Response`
- `app/wires/inbound/ai.py`: `Field` constraints, `to_generation_config`
- `app/wires/outbound/health.py`: nested outbound wire
