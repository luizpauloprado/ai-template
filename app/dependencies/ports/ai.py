from functools import partial
from typing import Annotated

from fastapi import Depends
from google import genai

from app.adapters.ai import gemini_adapter
from app.dependencies.resources import get_gemini_client
from app.dependencies.settings import SettingsDep
from app.domain.ports import GenerateText, GenerateTextWithConfig


def get_generate_text(
    client: Annotated[genai.Client, Depends(get_gemini_client)], settings: SettingsDep
) -> GenerateText:
    return partial(gemini_adapter.generate_text, client, settings.gemini_model)


def get_generate_text_with_config(
    client: Annotated[genai.Client, Depends(get_gemini_client)], settings: SettingsDep
) -> GenerateTextWithConfig:
    return partial(gemini_adapter.generate_text_with_config, client, settings.gemini_model)
