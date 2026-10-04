from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import SettingsDep, get_health_checks
from app.domain.ports import CheckComponent
from app.services import health_service
from app.wires.outbound.health import HealthOut, to_health_out

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(
    response: Response,
    checks: Annotated[dict[str, CheckComponent], Depends(get_health_checks)],
    settings: SettingsDep,
) -> HealthOut:
    result = await health_service.get_health(checks, settings.health_check_timeout_seconds)
    if result.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return to_health_out(result)
