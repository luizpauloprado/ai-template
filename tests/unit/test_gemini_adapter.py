import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from google.genai import types

from app.adapters.ai.gemini_adapter import ask, ask_with_config, extract_invoice, to_sdk_config
from app.domain.models import GenerationConfig, Invoice
from tests.fakes import make_invoice


def fake_client(text: str | None, model_version: str | None) -> AsyncMock:
    response = SimpleNamespace(text=text, model_version=model_version)
    client = AsyncMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_ask_maps_response() -> None:
    client = fake_client("oi", "gemini-x-001")

    generated = await ask(client, "gemini-x", "prompt")

    assert generated.text == "oi"
    assert generated.model == "gemini-x-001"
    client.aio.models.generate_content.assert_awaited_once_with(model="gemini-x", contents="prompt")


async def test_ask_handles_empty_response() -> None:
    generated = await ask(fake_client(None, None), "gemini-x", "prompt")

    assert generated.text == ""
    assert generated.model == "gemini-x"


def test_to_sdk_config_maps_only_provided_fields() -> None:
    sdk_config = to_sdk_config(GenerationConfig(system_instruction="seja breve", temperature=0.2))

    assert sdk_config.system_instruction == "seja breve"
    assert sdk_config.temperature == 0.2
    assert sdk_config.top_p is None
    assert sdk_config.max_output_tokens is None


async def test_ask_with_config_passes_config_to_client() -> None:
    client = fake_client("oi", "gemini-x-001")
    config = GenerationConfig(temperature=0.5, max_output_tokens=100)

    generated = await ask_with_config(client, "gemini-x", "prompt", config)

    assert generated.text == "oi"
    assert generated.model == "gemini-x-001"
    client.aio.models.generate_content.assert_awaited_once_with(
        model="gemini-x", contents="prompt", config=to_sdk_config(config)
    )


async def test_extract_invoice_maps_json_response() -> None:
    invoice = make_invoice()
    client = fake_client(invoice.model_dump_json(), "gemini-x-001")

    extracted = await extract_invoice(client, "gemini-x", b"%PDF-1.4", "extraia")

    assert extracted == invoice


async def test_extract_invoice_sends_pdf_and_schema() -> None:
    client = fake_client(make_invoice().model_dump_json(), "gemini-x-001")

    await extract_invoice(client, "gemini-x", b"%PDF-1.4", "extraia")

    kwargs = client.aio.models.generate_content.await_args.kwargs
    assert kwargs["model"] == "gemini-x"
    assert kwargs["contents"] == [
        types.Part.from_bytes(data=b"%PDF-1.4", mime_type="application/pdf"),
        "extraia",
    ]
    assert kwargs["config"].response_mime_type == "application/json"
    assert kwargs["config"].response_schema is Invoice
    assert kwargs["config"].temperature == 0


async def test_extract_invoice_logs_call(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app")
    client = fake_client(make_invoice().model_dump_json(), "gemini-x-001")

    await extract_invoice(client, "gemini-x", b"%PDF-1.4", "extraia")

    logger_name = "app.adapters.ai.gemini_adapter"
    messages = [r.getMessage() for r in caplog.records if r.name == logger_name]
    assert len(messages) == 1
    assert "extract_invoice model=gemini-x pdf_bytes=8" in messages[0]
