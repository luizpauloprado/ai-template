from functools import partial
from typing import Annotated

from fastapi import Depends

from app.adapters.ai import gemini_adapter
from app.dependencies.resources import GeminiClientDep
from app.dependencies.settings import SettingsDep
from app.domain.ports import Ask, AskWithConfig


def get_ask(client: GeminiClientDep, settings: SettingsDep) -> Ask:
    return partial(gemini_adapter.ask, client, settings.gemini_model)


def get_ask_with_config(client: GeminiClientDep, settings: SettingsDep) -> AskWithConfig:
    return partial(gemini_adapter.ask_with_config, client, settings.gemini_model)


AskDep = Annotated[Ask, Depends(get_ask)]
AskWithConfigDep = Annotated[AskWithConfig, Depends(get_ask_with_config)]
