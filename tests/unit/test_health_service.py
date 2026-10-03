import asyncio

from app.domain.models import ComponentStatus
from app.services.health_service import get_health
from tests.fakes import failing_check, fake_check

UP = ComponentStatus(status="up", version="1.0")


async def test_all_up_returns_ok() -> None:
    health = await get_health(
        {"database": fake_check(UP), "pgmq": fake_check(UP)}, timeout_seconds=1
    )

    assert health.status == "ok"
    assert set(health.components) == {"api", "database", "pgmq"}


async def test_down_component_returns_degraded() -> None:
    down = ComponentStatus(status="down", detail="not installed")
    health = await get_health({"database": fake_check(UP), "pgvector": fake_check(down)}, 1)

    assert health.status == "degraded"
    assert health.components["pgvector"].detail == "not installed"


async def test_exception_becomes_down() -> None:
    health = await get_health(
        {"database": failing_check(ConnectionError("boom"))}, timeout_seconds=1
    )

    assert health.status == "degraded"
    assert health.components["database"].status == "down"
    assert "boom" in (health.components["database"].detail or "")


async def test_timeout_becomes_down() -> None:
    async def slow() -> ComponentStatus:
        await asyncio.sleep(1)
        return UP

    health = await get_health({"database": slow}, timeout_seconds=0.01)

    assert health.components["database"].status == "down"
    assert "timeout" in (health.components["database"].detail or "")
