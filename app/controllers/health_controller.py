from fastapi import APIRouter, Response, status

from app.dependencies import HealthChecksDep, SettingsDep
from app.services import health_service
from app.wires.outbound.health import HealthOut, to_health_out

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(response: Response, checks: HealthChecksDep, settings: SettingsDep) -> HealthOut:
    result = await health_service.get_health(checks, settings.health_check_timeout_seconds)
    if result.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return to_health_out(result)
