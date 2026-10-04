import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors

from app.config import get_settings
from app.controllers import (
    ai_controller,
    external_controller,
    health_controller,
    items_controller,
    sample_controller,
)
from app.lifespan import lifespan
from app.logging_config import configure_logging, request_id_var

logger = logging.getLogger(__name__)


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Gera o request_id (ou usa o header X-Request-ID) e loga método, path, status e duração."""
    request_id = request.headers.get("x-request-id") or uuid4().hex[:12]
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("%s %s -> unhandled error", request.method, request.url.path)
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        level = (
            logging.ERROR
            if response.status_code >= 500
            else logging.WARNING
            if response.status_code >= 400
            else logging.INFO
        )
        logger.log(
            level,
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_var.reset(token)


async def handle_upstream_http_error(request: Request, exc: Exception) -> JSONResponse:
    # A mensagem completa (status, URL, corpo do provedor) vai só para o log.
    logger.error(
        "upstream error on %s %s: %s", request.method, request.url.path, exc, exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": f"upstream error: {type(exc).__name__}",
            "request_id": request_id_var.get(),
        },
    )


async def handle_upstream_timeout(request: Request, exc: Exception) -> JSONResponse:
    logger.error("upstream timeout on %s %s: %r", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "detail": f"upstream timeout: {type(exc).__name__}",
            "request_id": request_id_var.get(),
        },
    )


async def handle_gemini_error(request: Request, exc: Exception) -> JSONResponse:
    """Sobrecarga/cota (5xx, 429) que sobrou depois do retry do SDK vira 503 + Retry-After."""
    code = exc.code if isinstance(exc, genai_errors.APIError) else None
    if not isinstance(exc, genai_errors.ServerError) and code != 429:
        return await handle_upstream_http_error(request, exc)
    logger.error(
        "ai provider unavailable on %s %s: %s", request.method, request.url.path, exc, exc_info=exc
    )
    retry_after = max(1, round(get_settings().gemini_retry_max_delay_seconds))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        headers={"Retry-After": str(retry_after)},
        content={
            "detail": f"ai provider unavailable: {type(exc).__name__} {code}",
            "request_id": request_id_var.get(),
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.middleware("http")(log_requests)

    app.include_router(health_controller.router)
    app.include_router(ai_controller.router)
    app.include_router(external_controller.router)
    app.include_router(items_controller.router)
    app.include_router(sample_controller.router)

    app.add_exception_handler(httpx.HTTPError, handle_upstream_http_error)
    # o handler mais específico (pela MRO) vence: timeout -> 504 antes do HTTPError genérico
    app.add_exception_handler(httpx.TimeoutException, handle_upstream_timeout)
    app.add_exception_handler(genai_errors.APIError, handle_gemini_error)
    return app


app = create_app()
