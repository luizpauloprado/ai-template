# ai-template

Template de estudos de uma API em **FastAPI** que conversa com:

- **Gemini** (SDK `google-genai`)
- **Postgres 17** com **pgvector** e **PGMQ** (Postgres Message Queue)
- uma **API externa** via HTTP (JSONPlaceholder como exemplo)

A arquitetura é **hexagonal (ports & adapters)** em estilo funcional: só os modelos Pydantic são classes, todo o resto são funções com type hints.

---

## Arquitetura

```
HTTP ──▶ controller ──▶ wire-in (Pydantic) ──▶ service ──▶ port ──▶ adapter ──▶ Gemini / Postgres / HTTP
HTTP ◀── controller ◀── wire-out (Pydantic) ◀── service ◀──────────┘
```

| Camada          | Pasta                  | Responsabilidade                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Controllers** | `app/controllers/`     | Rotas FastAPI finas: recebem o wire-in, chamam o service e devolvem o wire-out. Traduzem `None` em 404.                                                                                                                                                                                                                                                        |
| **Wires**       | `app/wires/`           | Contratos HTTP de entrada (`inbound/`) e saída (`outbound/`), com as funções `to_*_out()` que convertem a partir do domínio.                                                                                                                                                                                                                                   |
| **Services**    | `app/services/`        | Regras de negócio. Recebem os **ports** como parâmetros e nunca importam adapters.                                                                                                                                                                                                                                                                             |
| **Domain**      | `app/domain/models.py` | Entidades (`Item`, `Post`, `HealthStatus`, …) imutáveis, sem nada de infraestrutura.                                                                                                                                                                                                                                                                           |
| **Ports**       | `app/domain/ports.py`  | Contratos como **aliases de `Callable`** (ex.: `GetItem = Callable[[int], Awaitable[Item \| None]]`).                                                                                                                                                                                                                                                          |
| **Adapters**    | `app/adapters/`        | Tudo o que é impuro: `ai/gemini_adapter.py`, `db/postgres_adapter.py`, `db/item_repository.py`, `http/external_api_client.py`.                                                                                                                                                                                                                                 |
| **Composição**  | `app/dependencies/`    | Liga ports a adapters com `functools.partial(adapter, pool_ou_client)`. Cada provider `get_<port>()` tem um alias `<Port>Dep = Annotated[<Port>, Depends(get_<port>)]`, e os controllers injetam **só** por esses aliases. `resources.py` lê os recursos de `app.state` (`PoolDep`, `HttpClientDep`, `GeminiClientDep`); `ports/<feature>.py` monta cada port. |
| **Lifespan**    | `app/lifespan.py`      | Cria e fecha o pool do Postgres, o `httpx.AsyncClient` e o client do Gemini, guardando-os em `app.state`.                                                                                                                                                                                                                                                      |

### Por que "wire"?

"Wire" é o formato do dado que **atravessa uma fronteira**, como em _wire format_. Há dois tipos:

- **Wires HTTP** (`app/wires/`): o contrato público da sua API.
- **Wires de adapter** (ex.: `app/adapters/http/external_api_schemas.py`): o formato de uma API de terceiros (com `userId` em camelCase etc.). Eles ficam **dentro do adapter**, que valida a resposta e devolve um modelo de domínio. Assim o formato de terceiros não vaza para o resto da aplicação.

### Por que funções em vez de classes?

Um port é só uma assinatura. Qualquer função compatível pode ser injetada: o adapter real em produção ou uma função fake no teste (veja `tests/fakes.py`). Para trocar o Postgres por outra coisa, basta escrever novas funções com a mesma assinatura e mudar o provider correspondente em `app/dependencies/ports/`.

---

## Estrutura

```
app/
  main.py                      create_app(), registro dos routers e handlers de erro (502)
  lifespan.py                  cria/fecha pool, http client e client do Gemini (em app.state)
  config.py                    Settings (pydantic-settings, lê .env)
  domain/
    models.py                  entidades imutáveis (Item, Post, HealthStatus, ...)
    ports.py                   ports como aliases de Callable
  services/                    regras de negócio (recebem ports como parâmetros)
    ai_service.py
    external_service.py
    health_service.py
    items_service.py
  wires/                       contratos HTTP
    inbound/                   request bodies: ai.py, items.py
    outbound/                  responses + to_*_out(): ai.py, external.py, health.py, items.py
  controllers/                 rotas FastAPI: ai, external, health, items (*_controller.py)
  dependencies/                composição ports <-> adapters (aliases *Dep)
    __init__.py                reexporta os providers get_* e os aliases *Dep
    settings.py                SettingsDep
    resources.py               get_db_pool, get_http_client, get_gemini_client (lêem app.state) + PoolDep, HttpClientDep, GeminiClientDep
    ports/                     um provider + alias *Dep por port: ai.py, external.py, health.py, items.py
  adapters/                    tudo o que é impuro
    ai/gemini_adapter.py
    db/postgres_adapter.py     pool + checks de health
    db/item_repository.py      SQL da tabela item
    http/external_api_client.py
    http/external_api_schemas.py   formato da API de terceiros (wire de adapter)
db/init/                       SQL executado na 1ª subida do banco
  01-extensions.sql            vector, pgmq e fila default
  02-item.sql                  tabela item
docker/postgres.Dockerfile     pgvector:pg17 + PGMQ compilado do fonte
Dockerfile                     imagem da API (python 3.13)
docker-compose.yml             serviços db + api
Makefile                       atalhos: install, up, down, reset, db, run, test*, lint
pyproject.toml                 config de pytest, ruff e mypy
requirements.txt               dependências de runtime
requirements-dev.txt           runtime + pytest, respx, ruff, mypy
.env.example                   modelo do .env
AGENTS.md                      guia para agentes de IA (regras, convenções, índice de skills)
CLAUDE.md                      importa o AGENTS.md (Claude Code)
.agents/skills/                skills por camada (templates e checklists); .claude/skills aponta para cá
tests/
  fakes.py                     implementações fake dos ports
  unit/                        services, wires e adapters (com mocks/respx)
  acceptance/                  endpoints via ASGI com dependency_overrides (sem banco)
  integration/                 repository e endpoints contra o Postgres real
```

---

## Pré-requisitos

- Docker + Docker Compose
- Python 3.13+ (para rodar a API ou os testes fora do Docker)
- (opcional) Uma chave do Gemini: https://aistudio.google.com/apikey

## Configuração

```bash
cp .env.example .env
# edite o .env e preencha GEMINI_API_KEY (opcional; sem ela, /ai/ask responde 503)
```

| Variável                                              | Default                                   | Uso                                                             |
| ----------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `app`                                     | credenciais do container                                        |
| `POSTGRES_PORT`                                       | `5432`                                    | porta exposta no host                                           |
| `DATABASE_URL`                                        | `postgresql://app:app@localhost:5432/app` | conexão da API. No compose, o host vira `db` automaticamente.   |
| `GEMINI_API_KEY`                                      | vazio                                     | chave do Gemini                                                 |
| `GEMINI_MODEL`                                        | `gemini-3.8-flash`                        | modelo usado                                                    |
| `EXTERNAL_API_BASE_URL`                               | `https://jsonplaceholder.typicode.com`    | API externa                                                     |
| `HTTP_TIMEOUT_SECONDS`                                | `10`                                      | timeout do httpx                                                |
| `HEALTH_CHECK_TIMEOUT_SECONDS`                        | `3`                                       | timeout de cada check do /health                                |
| `LOG_LEVEL`                                           | `INFO`                                    | nível dos logs no console (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Rodando

### Tudo no Docker (API + Postgres)

```bash
make up          # docker compose up --build -d
make logs        # logs da API
make down        # para tudo
make reset       # apaga o volume do banco e recria (re-executa db/init/*.sql)
```

A API sobe em http://localhost:8000 com `--reload`, porque `./app` é montado como volume. A documentação interativa fica em http://localhost:8000/docs.

### API local + Postgres no Docker

```bash
python3 -m venv venv
make install     # pip install -r requirements-dev.txt
make db          # sobe só o Postgres
make run         # uvicorn app.main:app --reload
```

> Os scripts de `db/init/` só rodam quando o volume está **vazio**. Se você alterar algum deles, rode `make reset`.

---

## Endpoints

| Método | Rota                       | Descrição                                                                                                                                   |
| ------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/health`                  | Status da API, do banco, do pgvector e do PGMQ. Responde 200 se tudo estiver `up` e 503 se algo estiver `down`.                             |
| POST   | `/ai/ask`                  | Gera texto com o Gemini                                                                                                                     |
| POST   | `/ai/ask/advanced`         | Gera texto com parâmetros de geração (`system_instruction`, `temperature`, `top_p`, `top_k`, `max_output_tokens`, `stop_sequences`, `seed`) |
| GET    | `/external/posts/{id}`     | Busca um post na API externa                                                                                                                |
| GET    | `/sample/extract-invoice`  | Lê a NF-e de exemplo (`app/services/invoice_sample.pdf`) e extrai os dados com o Gemini (JSON tipado)                                       |
| POST   | `/items`                   | Cria um item                                                                                                                                |
| GET    | `/items?limit=20&offset=0` | Lista os itens (paginado)                                                                                                                   |
| GET    | `/items/{id}`              | Busca um item                                                                                                                               |
| PUT    | `/items/{id}`              | Substitui `details` e atualiza `updated_at`                                                                                                 |
| DELETE | `/items/{id}`              | Remove um item                                                                                                                              |

```bash
curl localhost:8000/health
# {"status":"ok","components":{"api":{"status":"up",...},
#  "database":{"status":"up","version":"17.x"},
#  "pgvector":{"status":"up","version":"0.8.x"},
#  "pgmq":{"status":"up","version":"1.13.0","detail":"1 queue(s)"}}}

curl -X POST localhost:8000/items -H 'content-type: application/json' \
  -d '{"details": {"name": "primeiro", "tags": ["a", "b"]}}'
curl localhost:8000/items
curl -X PUT localhost:8000/items/1 -H 'content-type: application/json' -d '{"details": {"name": "editado"}}'
curl -X DELETE localhost:8000/items/1

curl localhost:8000/external/posts/1

curl -X POST localhost:8000/ai/ask -H 'content-type: application/json' \
  -d '{"prompt": "Explique arquitetura hexagonal em uma frase"}'

curl localhost:8000/sample/extract-invoice
# {"number":"000.001.234","series":"001","issuer":{"name":"EMPRESA EXEMPLO LTDA",...},
#  "items":[{"code":"3065","quantity":2.0,"unit_price":29.99,...}],"totals":{"invoice_total":59.98,...}}
```

Erros vindos de serviços externos (httpx ou Gemini) viram **502**. O corpo traz só o tipo do erro e o `request_id`; a mensagem completa fica no log:

```json
{ "detail": "upstream error: ClientError", "request_id": "f78ed767bbe2" }
```

---

## Logs

A API loga no console (stdout), no formato `data nível logger [request_id] mensagem`:

```
INFO    app.lifespan [-] gemini configurado (model=gemini-3.8-flash)
ERROR   app.main [f78ed767bbe2] upstream error on GET /sample/extract-invoice: 404 NOT_FOUND. {...'This model models/gemini-3.8-flash is no longer available...'}
Traceback (most recent call last): ...
ERROR   app.main [f78ed767bbe2] GET /sample/extract-invoice -> 502 (513.7 ms)
INFO    app.adapters.http.external_api_client [cb7a5de30c13] http GET https://jsonplaceholder.typicode.com/posts/1 -> 200 (49.8 ms)
INFO    app.main [cb7a5de30c13] GET /external/posts/1 -> 200 (52.1 ms)
```

- Toda requisição gera um `request_id`, devolvido no header `X-Request-ID` (se o cliente mandar esse header, o valor dele é reaproveitado). Para investigar um 502, procure no log pelo `request_id` do corpo da resposta.
- Cada request é logado com status e duração: `INFO` para 2xx/3xx, `WARNING` para 4xx e `ERROR` para 5xx.
- Também aparecem no log: startup/shutdown (`app.lifespan`), cada chamada ao Gemini com modelo e duração, cada chamada HTTP externa e os checks do `/health` que falharem.
- `LOG_LEVEL=DEBUG` mostra também a resposta bruta do Gemini.

---

## Banco de dados

Na primeira subida, `db/init/` executa:

- `01-extensions.sql`: `CREATE EXTENSION vector`, `CREATE EXTENSION pgmq` e cria a fila `default`.
- `02-item.sql`: cria a tabela `item`:

```sql
CREATE TABLE item (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    details    JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

O `updated_at` é atualizado explicitamente no SQL do `UPDATE` (`app/adapters/db/item_repository.py`).

Para acessar o banco:

```bash
docker compose exec db psql -U app -d app
# select * from pgmq.list_queues();
# select pgmq.send('default', '{"hello": "world"}');
# select * from pgmq.read('default', 30, 1);
```

> O PGMQ não tem pacote apt para arm64 no repositório PGDG. Por isso `docker/postgres.Dockerfile` baixa o fonte da versão `PGMQ_VERSION` e roda `make install`. Como é uma extensão só de SQL, a instalação é rápida.

---

## Testes

```bash
make test               # tudo
make test-unit          # services, wires e adapters (sem I/O real)
make test-acceptance    # endpoints via ASGI, com ports trocados por fakes
make test-integration   # contra o Postgres real (requer `make db`)
make test-gemini        # contra o Gemini real (requer GEMINI_API_KEY; fora do `make test`)
make lint               # ruff + mypy
```

- **Unit**: os services são testados com fakes de `tests/fakes.py`. O adapter HTTP é testado com `respx` e o do Gemini com `AsyncMock`.
- **Acceptance**: `create_app()` + `httpx.ASGITransport`, trocando os ports com `app.dependency_overrides`. Valida status codes e os contratos JSON.
- **Integration** (marker `integration`): usa o banco de verdade. Cada teste cria e apaga os próprios itens, então os dados que você já tem não são afetados. Se o Postgres não estiver acessível, esses testes são **pulados**.
- **Gemini** (marker `gemini`): manda o `invoice_sample.pdf` real para o Gemini e confere os campos extraídos. Fica fora do `make test` (custa chamadas de API) e é pulado sem `GEMINI_API_KEY`.

---

## Como adicionar uma nova entidade (seguindo o padrão de `item`)

1. **SQL**: crie `db/init/03-<tabela>.sql` e rode `make reset`, ou aplique o SQL manualmente.
2. **Domínio**: adicione o modelo em `app/domain/models.py` e os ports em `app/domain/ports.py`.
3. **Adapter**: crie `app/adapters/db/<entidade>_repository.py` com funções `async def x(pool, ...)`.
4. **Service**: crie `app/services/<entidade>_service.py`, que recebe os ports como parâmetros.
5. **Wires**: crie `app/wires/inbound/<entidade>.py` e `app/wires/outbound/<entidade>.py` (com a função `to_<entidade>_out`).
6. **Composição**: crie `app/dependencies/ports/<entidade>.py` com `get_<port>()` retornando `partial(repo_fn, pool)` e o alias `<Port>Dep = Annotated[<Port>, Depends(get_<port>)]`. Reexporte os dois em `app/dependencies/__init__.py`.
7. **Controller**: crie `app/controllers/<entidade>_controller.py` injetando os ports só pelos aliases `*Dep` (nada de `Depends` no controller) e registre o router em `app/main.py`.
8. **Testes**: adicione um fake em `tests/fakes.py`, testes unitários do service, testes de aceitação do endpoint e testes de integração do repository.
