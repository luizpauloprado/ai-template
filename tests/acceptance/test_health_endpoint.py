from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies import get_health_checks
from app.domain.models import ComponentStatus
from tests.fakes import failing_check, fake_check


async def test_health_ok(app: FastAPI, client: AsyncClient) -> None:
    up = fake_check(ComponentStatus(status="up", version="1.0"))
    app.dependency_overrides[get_health_checks] = lambda: {
        "database": up,
        "pgvector": up,
        "pgmq": up,
    }

    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body["components"]) == {"api", "database", "pgvector", "pgmq"}


async def test_health_degraded_returns_503(app: FastAPI, client: AsyncClient) -> None:
    up = fake_check(ComponentStatus(status="up"))
    app.dependency_overrides[get_health_checks] = lambda: {
        "database": up,
        "pgvector": up,
        "pgmq": failing_check(RuntimeError("pgmq off")),
    }

    response = await client.get("/health")

    assert response.status_code == 503
    assert response.json()["components"]["pgmq"]["status"] == "down"
