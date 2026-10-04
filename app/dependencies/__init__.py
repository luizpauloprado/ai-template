"""Composição: liga os ports (domínio) aos adapters (infra).

Cada função de `ports/` monta um port com `partial`, fechando sobre os recursos
criados no lifespan (pool, clients; veja `resources.py`), e tem um alias `*Dep`
que os controllers usam para injetá-la. Nos testes, basta sobrescrever as funções
`get_*` com `app.dependency_overrides`.
"""

from app.dependencies.ports.ai import AskDep, AskWithConfigDep, get_ask, get_ask_with_config
from app.dependencies.ports.external import FetchPostDep, get_fetch_post
from app.dependencies.ports.health import HealthChecksDep, get_health_checks
from app.dependencies.ports.items import (
    DeleteItemDep,
    GetItemDep,
    InsertItemDep,
    ListItemsDep,
    UpdateItemDep,
    get_delete_item,
    get_get_item,
    get_insert_item,
    get_list_items,
    get_update_item,
)
from app.dependencies.resources import (
    GeminiClientDep,
    HttpClientDep,
    PoolDep,
    get_db_pool,
    get_gemini_client,
    get_http_client,
)
from app.dependencies.settings import SettingsDep

__all__ = [
    "AskDep",
    "AskWithConfigDep",
    "DeleteItemDep",
    "FetchPostDep",
    "GeminiClientDep",
    "GetItemDep",
    "HealthChecksDep",
    "HttpClientDep",
    "InsertItemDep",
    "ListItemsDep",
    "PoolDep",
    "SettingsDep",
    "UpdateItemDep",
    "get_ask",
    "get_ask_with_config",
    "get_db_pool",
    "get_delete_item",
    "get_fetch_post",
    "get_gemini_client",
    "get_get_item",
    "get_health_checks",
    "get_http_client",
    "get_insert_item",
    "get_list_items",
    "get_update_item",
]
