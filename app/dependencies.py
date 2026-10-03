"""Composição: liga os ports (domínio) aos adapters (infra).

Cada função monta um port com `partial`, fechando sobre os recursos criados
no lifespan (pool, clients). Nos testes, basta sobrescrever estas funções com
`app.dependency_overrides`.
"""

from functools import partial
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from google import genai
from psycopg_pool import AsyncConnectionPool

from app.adapters.ai import gemini_adapter
from app.adapters.db import item_repository, postgres_adapter
from app.adapters.http import external_api_client
from app.config import Settings, get_settings
from app.domain.ports import (
    CheckComponent,
    DeleteItem,
    FetchPost,
    GenerateText,
    GetItem,
    InsertItem,
    ListItems,
    UpdateItem,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]


# --- Recursos (vivem em app.state, criados no lifespan) ---


def get_db_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.db_pool


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_gemini_client(request: Request) -> genai.Client:
    client: genai.Client | None = getattr(request.app.state, "gemini_client", None)
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "GEMINI_API_KEY não configurada")
    return client


PoolDep = Annotated[AsyncConnectionPool, Depends(get_db_pool)]


# --- Ports ---


def get_health_checks(pool: PoolDep) -> dict[str, CheckComponent]:
    return {
        "database": partial(postgres_adapter.check_database, pool),
        "pgvector": partial(postgres_adapter.check_pgvector, pool),
        "pgmq": partial(postgres_adapter.check_pgmq, pool),
    }


def get_generate_text(
    client: Annotated[genai.Client, Depends(get_gemini_client)], settings: SettingsDep
) -> GenerateText:
    return partial(gemini_adapter.generate_text, client, settings.gemini_model)


def get_fetch_post(client: Annotated[httpx.AsyncClient, Depends(get_http_client)]) -> FetchPost:
    return partial(external_api_client.fetch_post, client)


def get_insert_item(pool: PoolDep) -> InsertItem:
    return partial(item_repository.insert_item, pool)


def get_get_item(pool: PoolDep) -> GetItem:
    return partial(item_repository.get_item, pool)


def get_list_items(pool: PoolDep) -> ListItems:
    return partial(item_repository.list_items, pool)


def get_update_item(pool: PoolDep) -> UpdateItem:
    return partial(item_repository.update_item, pool)


def get_delete_item(pool: PoolDep) -> DeleteItem:
    return partial(item_repository.delete_item, pool)
