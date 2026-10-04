---
name: new-feature
description: Use when adding a new entity (DB table + CRUD endpoints) or a new endpoint backed by an external service, end to end. Gives the ordered list of files to create/edit across all layers and points to the layer skills for templates.
---

# New feature (vertical slice)

Templates in the skills use **`note`** as the example entity. Replace it consistently:

| Example | Replace with | Used in |
|---|---|---|
| `note` | entity, snake_case singular | table name, file names, function names |
| `notes` | plural, snake_case | router prefix `/notes`, list functions |
| `Note` | PascalCase | domain model, port names (`GetNote`), wires (`NoteIn`, `NoteOut`) |

## Variant A: new DB entity with CRUD

Do the steps **in order**. Each step names the exact file and the skill holding the template.

| # | File | Action | Skill |
|---|---|---|---|
| 1 | `db/init/NN-note.sql` (next free number) | `CREATE TABLE IF NOT EXISTS note (...)` | `postgres-adapter` |
| 2 | `app/domain/models.py` | Add `class Note(BaseModel)` with `frozen=True` | `domain-and-ports` |
| 3 | `app/domain/ports.py` | Add `InsertNote`, `GetNote`, `ListNotes`, `UpdateNote`, `DeleteNote` | `domain-and-ports` |
| 4 | `app/adapters/db/note_repository.py` | One `async def` per port, `pool` as first arg | `postgres-adapter` |
| 5 | `app/services/note_service.py` | One function per use case, ports as last args | `services` |
| 6 | `app/wires/inbound/note.py` | `NoteIn` (+ `to_<domain>` if it maps to a domain model) | `wires-and-controllers` |
| 7 | `app/wires/outbound/note.py` | `NoteOut` + `to_note_out` | `wires-and-controllers` |
| 8 | `app/dependencies/ports/note.py` | `get_*` providers + `*Dep` aliases | `composition` |
| 9 | `app/dependencies/__init__.py` | Re-export every `get_*` and `*Dep`, add to `__all__` | `composition` |
| 10 | `app/controllers/note_controller.py` | `router = APIRouter(prefix="/notes", tags=["notes"])` + routes | `wires-and-controllers` |
| 11 | `app/main.py` | `from app.controllers import ..., note_controller` and `app.include_router(note_controller.router)` | `wires-and-controllers` |
| 12 | `tests/fakes.py` | `make_fake_note_table()` | `testing` |
| 13 | `tests/unit/test_note_service.py` | Service tests with the fake | `testing` |
| 14 | `tests/acceptance/conftest.py` + `tests/acceptance/test_note_endpoint.py` | Override providers, test HTTP contract | `testing` |
| 15 | `tests/integration/test_note_repository.py` | Repository against real Postgres | `testing` |
| 16 | `README.md` | Endpoints table, DB section, structure tree | — |

Then run `make reset` (applies the new SQL; wipes local data), `make lint` and `make test`.

## Variant B: new endpoint backed by an external service (no DB)

| # | File | Action | Skill |
|---|---|---|---|
| 1 | `app/domain/models.py` + `app/domain/ports.py` | Domain model + port (e.g. `FetchUser`) | `domain-and-ports` |
| 2 | `app/adapters/http/<api>_schemas.py` | Third-party wire + `to_<domain>()` | `http-adapter` |
| 3 | `app/adapters/http/<api>_client.py` | `create_client()` (if a new base URL) + adapter functions | `http-adapter` |
| 4 | `app/config.py`, `.env.example`, `app/lifespan.py`, `app/dependencies/resources.py` | Only if a **new** client/resource is needed | `composition` |
| 5 | `app/services/<feature>_service.py` | Use case | `services` |
| 6 | `app/wires/outbound/<feature>.py` (+ inbound if it has a body) | Contracts | `wires-and-controllers` |
| 7 | `app/dependencies/ports/<feature>.py` + `__init__.py` | Provider + `*Dep` | `composition` |
| 8 | `app/controllers/<feature>_controller.py` + `app/main.py` | Route + `include_router` | `wires-and-controllers` |
| 9 | `tests/fakes.py`, `tests/unit/`, `tests/acceptance/` | Fake, adapter test with `respx`, service test, endpoint test | `testing` |

For a new LLM capability, follow Variant B but use the `ai-adapter` skill for steps 2–3.

## Final checklist

- [ ] No file in `domain/`, `services/` or `wires/` imports fastapi/httpx/psycopg/genai/adapters.
- [ ] The controller imports ports only as `*Dep` from `app.dependencies`.
- [ ] Every port has an adapter, a provider, a `*Dep` alias and a fake.
- [ ] The router is registered in `app/main.py`.
- [ ] `make lint` and `make test` pass.
- [ ] `README.md` is updated.

## Reference implementation

The `item` feature is the complete example. See `db/init/02-item.sql`, `app/domain/models.py` (`Item`), `app/domain/ports.py`, `app/adapters/db/item_repository.py`, `app/services/items_service.py`, `app/wires/inbound/items.py`, `app/wires/outbound/items.py`, `app/dependencies/ports/items.py`, `app/controllers/items_controller.py`, and `tests/**/test_item*`.
