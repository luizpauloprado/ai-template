"""Entidades de domínio. Não conhecem HTTP, banco nem SDKs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ComponentState = Literal["up", "down"]
OverallState = Literal["ok", "degraded"]


class ComponentStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ComponentState
    version: str | None = None
    detail: str | None = None


class HealthStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: OverallState
    components: dict[str, ComponentStatus]


class Item(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    details: dict[str, Any]
    updated_at: datetime


class Post(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    user_id: int
    title: str
    body: str


class GeneratedText(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model: str
