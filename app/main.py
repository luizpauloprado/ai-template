import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors

from app.config import get_settings
from app.controllers import ai_controller, external_controller, health_controller, items_controller
from app.lifespan import lifespan


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
