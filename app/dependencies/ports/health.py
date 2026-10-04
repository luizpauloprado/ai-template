from functools import partial

from app.adapters.db import postgres_adapter
from app.dependencies.resources import PoolDep
from app.domain.ports import CheckComponent


def get_health_checks(pool: PoolDep) -> dict[str, CheckComponent]:
    return {
        "database": partial(postgres_adapter.check_database, pool),
        "pgvector": partial(postgres_adapter.check_pgvector, pool),
        "pgmq": partial(postgres_adapter.check_pgmq, pool),
    }
