"""Adapter do Gemini (SDK google-genai)."""

import logging
import time

from google import genai
from google.genai import types

from app.domain.models import GeneratedText, GenerationConfig, Invoice

logger = logging.getLogger(__name__)


def create_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def to_sdk_config(config: GenerationConfig) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(**config.model_dump(exclude_none=True))


def _log_call(
    operation: str, model: str, started: float, response: types.GenerateContentResponse, info: str
) -> None:
    elapsed = time.perf_counter() - started
    logger.info("gemini %s model=%s %s took %.2fs", operation, model, info, elapsed)
    logger.debug("gemini %s raw response: %s", operation, response.text)


def _to_generated_text(response: types.GenerateContentResponse, model: str) -> GeneratedText:
    return GeneratedText(text=response.text or "", model=response.model_version or model)


async def ask(client: genai.Client, model: str, prompt: str) -> GeneratedText:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(model=model, contents=prompt)
    _log_call("ask", model, started, response, f"prompt_chars={len(prompt)}")
    return _to_generated_text(response, model)


async def ask_with_config(
    client: genai.Client, model: str, prompt: str, config: GenerationConfig
) -> GeneratedText:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model, contents=prompt, config=to_sdk_config(config)
    )
    _log_call("ask_with_config", model, started, response, f"prompt_chars={len(prompt)}")
    return _to_generated_text(response, model)


async def extract_invoice(client: genai.Client, model: str, pdf: bytes, prompt: str) -> Invoice:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=pdf, mime_type="application/pdf"), prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Invoice, temperature=0
        ),
    )
    _log_call("extract_invoice", model, started, response, f"pdf_bytes={len(pdf)}")
    return Invoice.model_validate_json(response.text or "{}")
