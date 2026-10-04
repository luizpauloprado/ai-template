from functools import partial
from typing import Annotated

from fastapi import Depends

from app.adapters.ai import gemini_adapter
from app.config import Settings
from app.dependencies.resources import GeminiClientDep
from app.dependencies.settings import SettingsDep
from app.domain.ports import Ask, AskWithConfig, ExtractInvoice


def _gemini_pricing(settings: Settings) -> gemini_adapter.GeminiPricing:
    return gemini_adapter.GeminiPricing(
        input_per_mtok=settings.gemini_input_price_per_mtok,
        output_per_mtok=settings.gemini_output_price_per_mtok,
    )


def get_ask(client: GeminiClientDep, settings: SettingsDep) -> Ask:
    return partial(gemini_adapter.ask, client, settings.gemini_model, _gemini_pricing(settings))


def get_ask_with_config(client: GeminiClientDep, settings: SettingsDep) -> AskWithConfig:
    return partial(
        gemini_adapter.ask_with_config, client, settings.gemini_model, _gemini_pricing(settings)
    )


def get_extract_invoice(client: GeminiClientDep, settings: SettingsDep) -> ExtractInvoice:
    return partial(
        gemini_adapter.extract_invoice, client, settings.gemini_model, _gemini_pricing(settings)
    )


AskDep = Annotated[Ask, Depends(get_ask)]
AskWithConfigDep = Annotated[AskWithConfig, Depends(get_ask_with_config)]
ExtractInvoiceDep = Annotated[ExtractInvoice, Depends(get_extract_invoice)]
