from pydantic import BaseModel

from app.domain.models import ComponentState, HealthStatus, OverallState


class ComponentStatusOut(BaseModel):
    status: ComponentState
    version: str | None = None
    detail: str | None = None


class HealthOut(BaseModel):
    status: OverallState
    components: dict[str, ComponentStatusOut]


def to_health_out(health: HealthStatus) -> HealthOut:
    return HealthOut(
        status=health.status,
        components={
            name: ComponentStatusOut(**component.model_dump())
            for name, component in health.components.items()
        },
    )
