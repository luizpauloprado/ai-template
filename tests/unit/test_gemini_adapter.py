from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.adapters.ai.gemini_adapter import generate_text


def fake_client(text: str | None, model_version: str | None) -> AsyncMock:
    response = SimpleNamespace(text=text, model_version=model_version)
    client = AsyncMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_generate_text_maps_response() -> None:
    client = fake_client("oi", "gemini-x-001")

    generated = await generate_text(client, "gemini-x", "prompt")

    assert generated.text == "oi"
    assert generated.model == "gemini-x-001"
    client.aio.models.generate_content.assert_awaited_once_with(model="gemini-x", contents="prompt")


async def test_generate_text_handles_empty_response() -> None:
    generated = await generate_text(fake_client(None, None), "gemini-x", "prompt")

    assert generated.text == ""
    assert generated.model == "gemini-x"
