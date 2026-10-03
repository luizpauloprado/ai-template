from typing import Any

from pydantic import BaseModel


class ItemIn(BaseModel):
    details: dict[str, Any]
