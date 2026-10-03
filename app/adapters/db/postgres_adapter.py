"""Adapter de infraestrutura do Postgres: pool de conexões e checks de saúde."""

from psycopg_pool import AsyncConnectionPool

from app.domain.models import ComponentStatus


async def create_pool(database_url: str) -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=10,
        open=False,
        # valida a conexão antes de entregar (recupera após restart do banco)
        check=AsyncConnectionPool.check_connection,
    )
    # wait=False: a API sobe mesmo com o banco fora; o /health mostra o problema
    await pool.open(wait=False)
    return pool


async def close_pool(pool: AsyncConnectionPool) -> None:
    await pool.close()


async def fetch_extension_version(pool: AsyncConnectionPool, extension: str) -> str | None:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = %s", (extension,)
        )
        row = await cursor.fetchone()
    return row[0] if row else None


async def check_database(pool: AsyncConnectionPool) -> ComponentStatus:
    async with pool.connection() as conn:
        cursor = await conn.execute("SHOW server_version")
        row = await cursor.fetchone()
    return ComponentStatus(status="up", version=row[0] if row else None)


async def check_pgvector(pool: AsyncConnectionPool) -> ComponentStatus:
    version = await fetch_extension_version(pool, "vector")
    if version is None:
        return ComponentStatus(status="down", detail="extension 'vector' not installed")
    return ComponentStatus(status="up", version=version)


async def check_pgmq(pool: AsyncConnectionPool) -> ComponentStatus:
    version = await fetch_extension_version(pool, "pgmq")
    if version is None:
        return ComponentStatus(status="down", detail="extension 'pgmq' not installed")

    async with pool.connection() as conn:
        cursor = await conn.execute("SELECT count(*) FROM pgmq.list_queues()")
        row = await cursor.fetchone()
    queues = row[0] if row else 0
    return ComponentStatus(status="up", version=version, detail=f"{queues} queue(s)")
