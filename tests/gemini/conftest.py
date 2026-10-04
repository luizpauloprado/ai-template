"""Testes contra o Gemini real (custam chamadas de API). Rode com `make test-gemini`."""

from collections.abc import AsyncIterator

import pytest
from google import genai

from app.adapters.ai.gemini_adapter import create_client
from app.config import get_settings


@pytest.fixture
async def gemini_client() -> AsyncIterator[genai.Client]:
    api_key = get_settings().gemini_api_key
    if not api_key:
        pytest.skip("GEMINI_API_KEY não configurada")

    client = create_client(api_key)
    yield client
    await client.aio.aclose()
