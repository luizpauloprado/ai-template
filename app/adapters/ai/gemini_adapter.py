"""Adapter do Gemini (SDK google-genai)."""

from google import genai

from app.domain.models import GeneratedText


def create_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


async def generate_text(client: genai.Client, model: str, prompt: str) -> GeneratedText:
    response = await client.aio.models.generate_content(model=model, contents=prompt)
    return GeneratedText(text=response.text or "", model=response.model_version or model)
