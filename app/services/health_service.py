import asyncio
import logging
from collections.abc import Mapping

from app.domain.models import ComponentStatus, HealthStatus
from app.domain.ports import CheckComponent

logger = logging.getLogger(__name__)


async def run_check(name: str, check: CheckComponent, timeout_seconds: float) -> ComponentStatus:
    try:
        return await asyncio.wait_for(check(), timeout=timeout_seconds)
    except TimeoutError:
        logger.warning("health check %s timed out after %ss", name, timeout_seconds)
        return ComponentStatus(status="down", detail=f"timeout after {timeout_seconds}s")
    except Exception as exc:  # noqa: BLE001 - health nunca deve quebrar
        logger.warning("health check %s failed: %s: %s", name, type(exc).__name__, exc)
        return ComponentStatus(status="down", detail=f"{type(exc).__name__}: {exc}")


async def get_health(checks: Mapping[str, CheckComponent], timeout_seconds: float) -> HealthStatus:
    names = list(checks)
    results = await asyncio.gather(
        *(run_check(name, checks[name], timeout_seconds) for name in names)
    )

    components = {"api": ComponentStatus(status="up"), **dict(zip(names, results, strict=True))}
    all_up = all(component.status == "up" for component in components.values())
    return HealthStatus(status="ok" if all_up else "degraded", components=components)
