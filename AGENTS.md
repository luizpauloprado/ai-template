# AGENTS.md

Instructions for AI coding agents working in this repository. Read this file fully before writing code.
For step-by-step recipes, load the matching skill from `.agents/skills/` (index at the bottom).

## What this is

FastAPI API template (Python 3.13) using **hexagonal architecture (ports & adapters) in a functional style**.
It talks to:

- **Gemini** via the `google-genai` SDK
- **Postgres 17** with **pgvector** and **PGMQ**, via a `psycopg` 3 async pool (`psycopg_pool`)
- an **external HTTP API** (JSONPlaceholder) via `httpx`

**The core rule:** Pydantic models are the only classes. Everything else is a plain function with type hints. A port is a `Callable` type alias. An adapter is a function whose first arguments are the resources it needs. `functools.partial` binds those resources, and FastAPI `Depends` injects the result.

## Commands

| Command | What it does |
|---|---|
| `make install` | `pip install -r requirements-dev.txt` into `venv/` (create it first: `python3 -m venv venv`) |
| `make db` | Start only Postgres in Docker (needed for `make run` and integration tests) |
| `make run` | Run the API locally with reload on http://localhost:8000 (docs at `/docs`) |
| `make up` / `make down` / `make logs` | Run API + Postgres in Docker / stop / tail API logs |
| `make reset` | Delete the DB volume and recreate it (re-runs `db/init/*.sql`) |
| `make lint` | `ruff check .` + `mypy app` |
| `make test` | All tests |
| `make test-unit` / `make test-acceptance` / `make test-integration` | One test layer |

`PY` defaults to `venv/bin/python`. Integration tests are **skipped** (not failed) when Postgres is unreachable.

## Request flow

```
HTTP ─▶ controller ─▶ wire-in (Pydantic) ─▶ service ─▶ port ─▶ adapter ─▶ Gemini / Postgres / HTTP
HTTP ◀─ controller ◀─ wire-out (Pydantic) ◀─ service ◀─ domain model ◀─┘
```

## Layers

| Layer | Path | Responsibility | May import from `app.` |
|---|---|---|---|
| Domain models | `app/domain/models.py` | Immutable entities (`frozen=True`). No infra. | `domain` only |
| Ports | `app/domain/ports.py` | Contracts as `Callable[..., Awaitable[...]]` aliases | `domain` only |
| Services | `app/services/<feature>_service.py` | Business logic. Receive ports as parameters. | `domain` only |
| Wires (HTTP) | `app/wires/inbound/<feature>.py`, `app/wires/outbound/<feature>.py` | Request/response contracts + `to_*` converters | `domain` only |
| Adapters | `app/adapters/{ai,db,http}/` | Everything impure: SQL, HTTP, SDK calls | `domain`, own package (e.g. `*_schemas.py`) |
| Composition | `app/dependencies/` | Binds ports to adapters with `partial`, exposes `*Dep` aliases | `adapters`, `domain`, `config` |
| Controllers | `app/controllers/<feature>_controller.py` | Thin FastAPI routes | `dependencies`, `services`, `wires`, `domain` |
| Lifespan | `app/lifespan.py` | Creates/closes pool and clients, stores them in `app.state` | `adapters`, `config` |
| App | `app/main.py` | `create_app()`, router registration, exception handlers | `controllers`, `lifespan`, `config` |
| Config | `app/config.py` | `Settings` (pydantic-settings, reads `.env`) | nothing |

### Import rules (MUST follow)

- `domain/`, `services/` and `wires/` MUST NOT import `fastapi`, `httpx`, `psycopg`, `google.genai`, adapters, or `dependencies`.
- Only `dependencies/` and `lifespan.py` import from `adapters/`. Controllers never import adapters.
- Controllers MUST get ports through `*Dep` aliases imported from `app.dependencies` (the package, not submodules).
- `Depends(...)` appears **only** on the line that defines a `*Dep` alias in `app/dependencies/`. Never write `Annotated[X, Depends(get_x)]` in a controller or a provider signature; use the alias. (`Annotated[int, Path(...)]` / `Query(...)` for validation is fine.)
- Third-party payload formats (e.g. camelCase fields) stay inside the adapter (`*_schemas.py`). The adapter returns domain models.

## Conventions

- **No classes** except Pydantic models. No service classes, repository classes or DI containers.
- **Domain models** use `model_config = ConfigDict(frozen=True)`. Use `Literal[...]` aliases for enums.
- **Ports** live in `app/domain/ports.py`, grouped by a `# <Feature>` comment and named `VerbNoun` (`GetItem`, `FetchPost`). When positional arguments are ambiguous, document them: `ListItems = Callable[[int, int], Awaitable[list[Item]]]  # (limit, offset)`.
- **Adapter signature:** resources first, then the port arguments: `async def get_item(pool: AsyncConnectionPool, item_id: int) -> Item | None`. `partial(get_item, pool)` must match the port exactly.
- **Service signature:** data arguments first, ports last: `async def get_item(item_id: int, get: GetItem) -> Item | None`.
- **Providers** in `app/dependencies/ports/<feature>.py`: `def get_<port_snake>(...) -> Port` returning a `partial`, plus `<Port>Dep = Annotated[<Port>, Depends(get_<port_snake>)]`. Both are re-exported in `app/dependencies/__init__.py` (`get_*` is needed for `dependency_overrides` in tests).
- **Existing `*Dep` aliases** (all importable from `app.dependencies`):
  - Resources: `SettingsDep`, `PoolDep`, `HttpClientDep`, `GeminiClientDep`
  - Ports: `AskDep`, `AskWithConfigDep`, `FetchPostDep`, `HealthChecksDep`, `InsertItemDep`, `GetItemDep`, `ListItemsDep`, `UpdateItemDep`, `DeleteItemDep`
- **Converters:** `to_<x>_out(domain) -> XOut` in outbound wires, `to_<domain>(wire_in)` in inbound wires, `to_<domain>(row_or_wire)` in adapters.
- **Naming:** `<feature>_controller.py`, `<feature>_service.py`, `<entity>_repository.py`, `<api>_client.py` + `<api>_schemas.py`. Inbound wires `XIn`, outbound wires `XOut`.
- All I/O is `async`. Full type hints everywhere (mypy runs on `app/`). Ruff line length 100, rules `E,F,I,B,UP,ASYNC`.
- Use modern typing: `X | None`, `list[...]`, `dict[...]`, `collections.abc.Callable/Awaitable`.
- Short docstrings/comments, and only where the code is not obvious. Match the surrounding code (existing comments are in Portuguese; new ones may be in either language).

## Error mapping

| Situation | Where | HTTP |
|---|---|---|
| Service returns `None` (not found) | Controller (`ensure_found` / `HTTPException`) | 404 |
| Delete port returns `False` | Controller | 404 |
| Invalid body/path/query | Pydantic/FastAPI automatically | 422 |
| `httpx.HTTPError` or `google.genai.errors.APIError` escapes | Handler in `app/main.py` | 502 |
| Optional resource missing (no `GEMINI_API_KEY`) | `get_gemini_client` in `app/dependencies/resources.py` | 503 |
| Health has a component `down` | `health_controller` | 503 |

Do not catch infrastructure exceptions in services or controllers. Let them reach the handlers in `main.py`. To map a new upstream exception type, register it there with `app.add_exception_handler(...)`.

## Endpoints

| Method | Path | Controller |
|---|---|---|
| GET | `/health` | `health_controller.py` |
| POST | `/ai/ask` | `ai_controller.py` |
| POST | `/ai/ask/advanced` | `ai_controller.py` (accepts generation config) |
| GET | `/external/posts/{post_id}` | `external_controller.py` |
| POST / GET | `/items`, `/items?limit=&offset=` | `items_controller.py` |
| GET / PUT / DELETE | `/items/{item_id}` | `items_controller.py` |

## Configuration

1. Add the field with a default to `Settings` in `app/config.py` (snake_case; the env var is the UPPER_CASE name).
2. Add it to `.env.example` and to the variables table in `README.md`.
3. Read it through `SettingsDep` (controllers/providers) or `get_settings()` (lifespan). Never read `os.environ` directly.

## Gotchas

- `db/init/*.sql` runs **only when the DB volume is empty**. After adding or changing a file there, run `make reset` (this wipes data).
- `get_settings()` is `lru_cache`d, so changing `.env` requires restarting the app.
- Resources (`db_pool`, `http_client`, `gemini_client`) live in `app.state` and are created in `app/lifespan.py`. The pool opens with `wait=False`, so the API starts even without the DB.
- Acceptance tests build `create_app()` **without running the lifespan**. Every port a tested route uses must be overridden through `app.dependency_overrides`.
- The `api` container mounts `./app` only. Changes to `requirements.txt` require `make up` (rebuild).

## Definition of done

1. `make lint` passes with no errors.
2. `make test` passes (run `make db` first so the integration tests actually run).
3. New behavior has tests in the right layers: a fake in `tests/fakes.py`, a unit test for the service, an acceptance test for the endpoint, and an integration test for any SQL.
4. `README.md` is updated when endpoints, env vars or DB tables change.

## Skills (`.agents/skills/`)

Load the skill before touching the corresponding layer.

| Skill | Load when |
|---|---|
| `new-feature` | Adding a new entity/CRUD or a new endpoint end to end. Start here; it orchestrates the others. |
| `domain-and-ports` | Adding or changing domain models or port signatures |
| `services` | Writing business logic in `app/services/` |
| `wires-and-controllers` | Adding request/response contracts or routes |
| `composition` | Wiring ports to adapters, adding a resource to the lifespan, adding settings |
| `postgres-adapter` | Writing SQL, repositories, `db/init` scripts, health checks, pgvector/pgmq |
| `http-adapter` | Calling a third-party HTTP API |
| `ai-adapter` | Changing the Gemini integration or adding generation options/capabilities |
| `testing` | Writing fakes and unit/acceptance/integration tests |
