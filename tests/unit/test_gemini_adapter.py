import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from google.genai import types

from app.adapters.ai.gemini_adapter import (
    GeminiPricing,
    ask,
    ask_with_config,
    extract_invoice,
    to_sdk_config,
)
from app.domain.models import GenerationConfig, Invoice
from tests.fakes import make_invoice

NO_PRICING = GeminiPricing()


def usage(
    tokens_in: int, tokens_out: int, thinking: int | None = None, cached: int | None = None
) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_token_count=tokens_in,
        candidates_token_count=tokens_out,
        thoughts_token_count=thinking,
        cached_content_token_count=cached,
        total_token_count=tokens_in + tokens_out + (thinking or 0),
    )


def fake_client(
    text: str | None, model_version: str | None, usage_metadata: SimpleNamespace | None = None
) -> AsyncMock:
    response = SimpleNamespace(
        text=text, model_version=model_version, usage_metadata=usage_metadata
    )
    client = AsyncMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_ask_maps_response() -> None:
    client = fake_client("oi", "gemini-x-001")

    generated = await ask(client, "gemini-x", NO_PRICING, "prompt")

    assert generated.text == "oi"
    assert generated.model == "gemini-x-001"
    client.aio.models.generate_content.assert_awaited_once_with(model="gemini-x", contents="prompt")


async def test_ask_handles_empty_response() -> None:
    generated = await ask(fake_client(None, None), "gemini-x", NO_PRICING, "prompt")

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

    generated = await ask_with_config(client, "gemini-x", NO_PRICING, "prompt", config)

    assert generated.text == "oi"
    assert generated.model == "gemini-x-001"
    client.aio.models.generate_content.assert_awaited_once_with(
        model="gemini-x", contents="prompt", config=to_sdk_config(config)
    )


async def test_extract_invoice_maps_json_response() -> None:
    invoice = make_invoice()
    client = fake_client(invoice.model_dump_json(), "gemini-x-001")

    extracted = await extract_invoice(client, "gemini-x", NO_PRICING, b"%PDF-1.4", "extraia")

    assert extracted == invoice


async def test_extract_invoice_sends_pdf_and_schema() -> None:
    client = fake_client(make_invoice().model_dump_json(), "gemini-x-001")

    await extract_invoice(client, "gemini-x", NO_PRICING, b"%PDF-1.4", "extraia")

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

    await extract_invoice(client, "gemini-x", NO_PRICING, b"%PDF-1.4", "extraia")

    logger_name = "app.adapters.ai.gemini_adapter"
    messages = [r.getMessage() for r in caplog.records if r.name == logger_name]
    assert len(messages) == 1
    assert "extract_invoice model=gemini-x pdf_bytes=8" in messages[0]


def gemini_log_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "app.adapters.ai.gemini_adapter"]


async def test_call_logs_tokens_without_cost_when_no_pricing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app")
    client = fake_client("oi", "gemini-x-001", usage(120, 30, thinking=50, cached=10))

    await ask(client, "gemini-x", NO_PRICING, "prompt")

    [message] = gemini_log_messages(caplog)
    assert (
        "tokens_in=120 tokens_out=30 tokens_thinking=50 tokens_cached=10 tokens_total=200"
        in message
    )
    assert "cost_usd" not in message


async def test_call_logs_estimated_cost(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app")
    pricing = GeminiPricing(input_per_mtok=0.30, output_per_mtok=2.50)
    client = fake_client("oi", "gemini-x-001", usage(1_000_000, 100_000, thinking=100_000))

    await ask(client, "gemini-x", pricing, "prompt")

    # 1M * 0.30 + (100k + 100k) * 2.50 / 1M = 0.30 + 0.50
    [message] = gemini_log_messages(caplog)
    assert "cost_usd=0.800000" in message


async def test_call_without_usage_metadata_logs_zero_tokens(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app")

    await ask(fake_client("oi", None), "gemini-x", GeminiPricing(input_per_mtok=1), "prompt")

    [message] = gemini_log_messages(caplog)
    assert "tokens_in=0 tokens_out=0 tokens_thinking=0 tokens_cached=0 tokens_total=0" in message
    assert "cost_usd=0.000000" in message
