"""Adapter do Gemini (SDK google-genai)."""

import logging
import time

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict

from app.domain.models import GeneratedText, GenerationConfig, Invoice

logger = logging.getLogger(__name__)


# Erros transitórios: timeout, rate limit/cota, modelo sobrecarregado e afins.
RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]


class GeminiRetry(BaseModel):
    """Timeout por tentativa e retry com backoff exponencial + jitter (feito pelo próprio SDK)."""

    model_config = ConfigDict(frozen=True)

    timeout_seconds: float = 60.0
    attempts: int = 3  # inclui a primeira chamada
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 10.0


def to_http_options(retry: GeminiRetry) -> types.HttpOptions:
    return types.HttpOptions(
        timeout=int(retry.timeout_seconds * 1000),  # o SDK usa milissegundos
        retry_options=types.HttpRetryOptions(
            attempts=retry.attempts,
            initial_delay=retry.initial_delay_seconds,
            max_delay=retry.max_delay_seconds,
            http_status_codes=RETRYABLE_STATUS_CODES,
        ),
    )


def create_client(api_key: str, retry: GeminiRetry | None = None) -> genai.Client:
    return genai.Client(api_key=api_key, http_options=to_http_options(retry or GeminiRetry()))


def to_sdk_config(config: GenerationConfig) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(**config.model_dump(exclude_none=True))


class GeminiPricing(BaseModel):
    """Preço em USD por 1M tokens, só para estimar o custo no log."""

    model_config = ConfigDict(frozen=True)

    input_per_mtok: float = 0.0
    output_per_mtok: float = 0.0


def _usage_info(response: types.GenerateContentResponse, pricing: GeminiPricing) -> str:
    usage = response.usage_metadata
    tokens_in = (usage and usage.prompt_token_count) or 0
    tokens_out = (usage and usage.candidates_token_count) or 0
    tokens_thinking = (usage and usage.thoughts_token_count) or 0
    tokens_cached = (usage and usage.cached_content_token_count) or 0
    tokens_total = (usage and usage.total_token_count) or 0
    info = (
        f"tokens_in={tokens_in} tokens_out={tokens_out} tokens_thinking={tokens_thinking} "
        f"tokens_cached={tokens_cached} tokens_total={tokens_total}"
    )
    if pricing.input_per_mtok or pricing.output_per_mtok:
        # Estimativa: thinking é cobrado como saída; cache entra com preço cheio (sem desconto).
        cost = (
            tokens_in * pricing.input_per_mtok
            + (tokens_out + tokens_thinking) * pricing.output_per_mtok
        ) / 1_000_000
        info += f" cost_usd={cost:.6f}"
    return info


def _log_call(
    operation: str,
    model: str,
    pricing: GeminiPricing,
    started: float,
    response: types.GenerateContentResponse,
    info: str,
) -> None:
    # inclui o tempo das tentativas anteriores e das esperas do retry
    elapsed = time.perf_counter() - started
    usage = _usage_info(response, pricing)
    logger.info("gemini %s model=%s %s %s took %.2fs", operation, model, info, usage, elapsed)
    logger.debug("gemini %s raw response: %s", operation, response.text)


def _to_generated_text(response: types.GenerateContentResponse, model: str) -> GeneratedText:
    return GeneratedText(text=response.text or "", model=response.model_version or model)


async def ask(
    client: genai.Client, model: str, pricing: GeminiPricing, prompt: str
) -> GeneratedText:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(model=model, contents=prompt)
    _log_call("ask", model, pricing, started, response, f"prompt_chars={len(prompt)}")
    return _to_generated_text(response, model)


async def ask_with_config(
    client: genai.Client,
    model: str,
    pricing: GeminiPricing,
    prompt: str,
    config: GenerationConfig,
) -> GeneratedText:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model, contents=prompt, config=to_sdk_config(config)
    )
    _log_call("ask_with_config", model, pricing, started, response, f"prompt_chars={len(prompt)}")
    return _to_generated_text(response, model)


async def extract_invoice(
    client: genai.Client, model: str, pricing: GeminiPricing, pdf: bytes, prompt: str
) -> Invoice:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=pdf, mime_type="application/pdf"), prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Invoice, temperature=0
        ),
    )
    _log_call("extract_invoice", model, pricing, started, response, f"pdf_bytes={len(pdf)}")
    return Invoice.model_validate_json(response.text or "{}")
