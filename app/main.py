from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors

from app.adapters.ai import gemini_adapter
from app.adapters.db import postgres_adapter
from app.adapters.http import external_api_client
from app.config import get_settings
from app.controllers import ai_controller, external_controller, health_controller, items_controller


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
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await postgres_adapter.close_pool(app.state.db_pool)


async def handle_upstream_http_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"upstream error: {type(exc).__name__}"},
    )


def create_app() -> FastAPI:
    app = FastAPI(title=get_settings().app_name, lifespan=lifespan)

    app.include_router(health_controller.router)
    app.include_router(ai_controller.router)
    app.include_router(external_controller.router)
    app.include_router(items_controller.router)

    app.add_exception_handler(httpx.HTTPError, handle_upstream_http_error)
    app.add_exception_handler(genai_errors.APIError, handle_upstream_http_error)
    return app


app = create_app()
