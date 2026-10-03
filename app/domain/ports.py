"""Ports: contratos que o núcleo (services) espera do mundo externo.

São apenas assinaturas de função. Qualquer função com a mesma assinatura
(adapter real, fake de teste, etc.) pode ser injetada.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from app.domain.models import ComponentStatus, GeneratedText, Item, Post

# Health
CheckComponent = Callable[[], Awaitable[ComponentStatus]]

# AI
GenerateText = Callable[[str], Awaitable[GeneratedText]]

# API externa
FetchPost = Callable[[int], Awaitable[Post | None]]

# Repository de Item
InsertItem = Callable[[dict[str, Any]], Awaitable[Item]]
GetItem = Callable[[int], Awaitable[Item | None]]
ListItems = Callable[[int, int], Awaitable[list[Item]]]  # (limit, offset)
UpdateItem = Callable[[int, dict[str, Any]], Awaitable[Item | None]]
DeleteItem = Callable[[int], Awaitable[bool]]
