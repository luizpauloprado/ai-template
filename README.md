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

| Camada | Pasta | Responsabilidade |
|---|---|---|
| **Controllers** | `app/controllers/` | Rotas FastAPI finas: recebem o wire-in, chamam o service e devolvem o wire-out. Traduzem `None` em 404. |
| **Wires** | `app/wires/` | Contratos HTTP de entrada (`*_in.py`) e saída (`*_out.py`), com as funções `to_*_out()` que convertem a partir do domínio. |
| **Services** | `app/services/` | Regras de negócio. Recebem os **ports** como parâmetros e nunca importam adapters. |
| **Domain** | `app/domain/models.py` | Entidades (`Item`, `Post`, `HealthStatus`, …) imutáveis, sem nada de infraestrutura. |
| **Ports** | `app/domain/ports.py` | Contratos como **aliases de `Callable`** (ex.: `GetItem = Callable[[int], Awaitable[Item \| None]]`). |
| **Adapters** | `app/adapters/` | Tudo o que é impuro: `ai/gemini_adapter.py`, `db/postgres_adapter.py`, `db/item_repository.py`, `http/external_api_client.py`. |
| **Composição** | `app/dependencies.py` | Liga ports a adapters com `functools.partial(adapter, pool_ou_client)` e os injeta via `Depends`. |
| **Lifespan** | `app/main.py` | Cria e fecha o pool do Postgres, o `httpx.AsyncClient` e o client do Gemini, guardando-os em `app.state`. |

### Por que "wire"?

"Wire" é o formato do dado que **atravessa uma fronteira**, como em *wire format*. Há dois tipos:

- **Wires HTTP** (`app/wires/`): o contrato público da sua API.
- **Wires de adapter** (ex.: `app/adapters/http/external_api_wires.py`): o formato de uma API de terceiros (com `userId` em camelCase etc.). Eles ficam **dentro do adapter**, que valida a resposta e devolve um modelo de domínio. Assim o formato de terceiros não vaza para o resto da aplicação.

### Por que funções em vez de classes?

Um port é só uma assinatura. Qualquer função compatível pode ser injetada: o adapter real em produção ou uma função fake no teste (veja `tests/fakes.py`). Para trocar o Postgres por outra coisa, basta escrever novas funções com a mesma assinatura e mudar `dependencies.py`.

---

## Estrutura

```
app/
  main.py               create_app(), lifespan, handlers de erro
  config.py             Settings (pydantic-settings, lê .env)
  dependencies.py       composição ports ↔ adapters
  domain/               models.py, ports.py
  services/             health, ai, items, external
  wires/                *_in.py / *_out.py
  controllers/          health, ai, items, external
  adapters/
    ai/gemini_adapter.py
    db/postgres_adapter.py     pool + checks de health
    db/item_repository.py      SQL da tabela item
    http/external_api_client.py
    http/external_api_wires.py
db/init/                SQL executado na 1ª subida do banco (extensões, fila, tabela item)
docker/postgres.Dockerfile     pgvector:pg17 + PGMQ compilado do fonte
Dockerfile              imagem da API (python 3.13)
docker-compose.yml      serviços db + api
tests/
  fakes.py              implementações fake dos ports
  unit/                 services, wires e adapters (com mocks/respx)
  acceptance/           endpoints via ASGI com dependency_overrides (sem banco)
  integration/          repository e endpoints contra o Postgres real
```

---

## Pré-requisitos

- Docker + Docker Compose
- Python 3.13+ (para rodar a API ou os testes fora do Docker)
- (opcional) Uma chave do Gemini: https://aistudio.google.com/apikey

## Configuração

```bash
cp .env.example .env
# edite o .env e preencha GEMINI_API_KEY (opcional; sem ela, /ai/generate responde 503)
```

| Variável | Default | Uso |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `app` | credenciais do container |
| `POSTGRES_PORT` | `5432` | porta exposta no host |
| `DATABASE_URL` | `postgresql://app:app@localhost:5432/app` | conexão da API. No compose, o host vira `db` automaticamente. |
| `GEMINI_API_KEY` | vazio | chave do Gemini |
| `GEMINI_MODEL` | `gemini-2.5-flash` | modelo usado |
| `EXTERNAL_API_BASE_URL` | `https://jsonplaceholder.typicode.com` | API externa |
| `HTTP_TIMEOUT_SECONDS` | `10` | timeout do httpx |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | `3` | timeout de cada check do /health |

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

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API, do banco, do pgvector e do PGMQ. Responde 200 se tudo estiver `up` e 503 se algo estiver `down`. |
| POST | `/ai/generate` | Gera texto com o Gemini |
| GET | `/external/posts/{id}` | Busca um post na API externa |
| POST | `/items` | Cria um item |
| GET | `/items?limit=20&offset=0` | Lista os itens (paginado) |
| GET | `/items/{id}` | Busca um item |
| PUT | `/items/{id}` | Substitui `details` e atualiza `updated_at` |
| DELETE | `/items/{id}` | Remove um item |

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

curl -X POST localhost:8000/ai/generate -H 'content-type: application/json' \
  -d '{"prompt": "Explique arquitetura hexagonal em uma frase"}'
```

Erros vindos de serviços externos (httpx ou Gemini) viram **502**.

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
make lint               # ruff + mypy
```

- **Unit**: os services são testados com fakes de `tests/fakes.py`. O adapter HTTP é testado com `respx` e o do Gemini com `AsyncMock`.
- **Acceptance**: `create_app()` + `httpx.ASGITransport`, trocando os ports com `app.dependency_overrides`. Valida status codes e os contratos JSON.
- **Integration** (marker `integration`): usa o banco de verdade. Cada teste cria e apaga os próprios itens, então os dados que você já tem não são afetados. Se o Postgres não estiver acessível, esses testes são **pulados**.

---

## Como adicionar uma nova entidade (seguindo o padrão de `item`)

1. **SQL**: crie `db/init/03-<tabela>.sql` e rode `make reset`, ou aplique o SQL manualmente.
2. **Domínio**: adicione o modelo em `app/domain/models.py` e os ports em `app/domain/ports.py`.
3. **Adapter**: crie `app/adapters/db/<entidade>_repository.py` com funções `async def x(pool, ...)`.
4. **Service**: crie `app/services/<entidade>_service.py`, que recebe os ports como parâmetros.
5. **Wires**: crie `app/wires/<entidade>_in.py` e `<entidade>_out.py` (com a função `to_<entidade>_out`).
6. **Composição**: em `app/dependencies.py`, adicione `get_<port>()` retornando `partial(repo_fn, pool)`.
7. **Controller**: crie `app/controllers/<entidade>_controller.py` e registre o router em `app/main.py`.
8. **Testes**: adicione um fake em `tests/fakes.py`, testes unitários do service, testes de aceitação do endpoint e testes de integração do repository.
