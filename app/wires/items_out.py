from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.models import Item


class ItemOut(BaseModel):
    id: int
    details: dict[str, Any]
    updated_at: datetime


def to_item_out(item: Item) -> ItemOut:
    return ItemOut(id=item.id, details=item.details, updated_at=item.updated_at)
