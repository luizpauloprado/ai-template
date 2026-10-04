import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.ai import gemini_adapter
from app.adapters.db import postgres_adapter
from app.adapters.http import external_api_client
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.db_pool = await postgres_adapter.create_pool(settings.database_url)
    app.state.http_client = external_api_client.create_client(
        settings.external_api_base_url, settings.http_timeout_seconds
    )
    app.state.gemini_client = (
        gemini_adapter.create_client(settings.gemini_api_key) if settings.gemini_api_key else None
    )
    logger.info("starting %s (env=%s)", settings.app_name, settings.app_env)
    logger.info("external api: %s", settings.external_api_base_url)
    if app.state.gemini_client is None:
        logger.warning("GEMINI_API_KEY ausente: endpoints de IA vão responder 503")
    else:
        logger.info("gemini configurado (model=%s)", settings.gemini_model)
    try:
        yield
    finally:
        logger.info("shutting down")
        await app.state.http_client.aclose()
        await postgres_adapter.close_pool(app.state.db_pool)
