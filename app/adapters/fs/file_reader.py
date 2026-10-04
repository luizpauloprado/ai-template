"""Adapter de leitura de arquivos locais."""

import asyncio
from pathlib import Path


async def read_bytes(path: Path) -> bytes:
    # Leitura em thread para não bloquear o event loop.
    return await asyncio.to_thread(path.read_bytes)
