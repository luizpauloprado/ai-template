"""Composição: liga os ports (domínio) aos adapters (infra).

Cada função de `ports/` monta um port com `partial`, fechando sobre os recursos
criados no lifespan (pool, clients; veja `resources.py`). Nos testes, basta
sobrescrever estas funções com `app.dependency_overrides`.
"""

from app.dependencies.ports.ai import get_generate_text
from app.dependencies.ports.external import get_fetch_post
from app.dependencies.ports.health import get_health_checks
from app.dependencies.ports.items import (
    get_delete_item,
    get_get_item,
    get_insert_item,
    get_list_items,
    get_update_item,
)
from app.dependencies.resources import PoolDep, get_db_pool, get_gemini_client, get_http_client
from app.dependencies.settings import SettingsDep

__all__ = [
    "PoolDep",
    "SettingsDep",
    "get_db_pool",
    "get_delete_item",
    "get_fetch_post",
    "get_gemini_client",
    "get_generate_text",
    "get_get_item",
    "get_health_checks",
    "get_http_client",
    "get_insert_item",
    "get_list_items",
    "get_update_item",
]
