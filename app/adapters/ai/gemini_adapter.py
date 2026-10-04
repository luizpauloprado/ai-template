"""Adapter do Gemini (SDK google-genai)."""

from google import genai
from google.genai import types

from app.domain.models import GeneratedText, GenerationConfig


def create_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def to_sdk_config(config: GenerationConfig) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(**config.model_dump(exclude_none=True))


def _to_generated_text(response: types.GenerateContentResponse, model: str) -> GeneratedText:
    return GeneratedText(text=response.text or "", model=response.model_version or model)


async def generate_text(client: genai.Client, model: str, prompt: str) -> GeneratedText:
    response = await client.aio.models.generate_content(model=model, contents=prompt)
    return _to_generated_text(response, model)


async def generate_text_with_config(
    client: genai.Client, model: str, prompt: str, config: GenerationConfig
) -> GeneratedText:
    response = await client.aio.models.generate_content(
        model=model, contents=prompt, config=to_sdk_config(config)
    )
    return _to_generated_text(response, model)
