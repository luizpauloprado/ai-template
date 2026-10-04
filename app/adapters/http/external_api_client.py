"""Adapter HTTP para a API externa."""

import logging
import time

import httpx

from app.adapters.http.external_api_schemas import ExternalPostWire, to_post
from app.domain.models import Post

logger = logging.getLogger(__name__)


async def _mark_start(request: httpx.Request) -> None:
    request.extensions["started_at"] = time.perf_counter()


async def _log_response(response: httpx.Response) -> None:
    request = response.request
    started = request.extensions.get("started_at", time.perf_counter())
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "http %s %s -> %d (%.1f ms)", request.method, request.url, response.status_code, elapsed_ms
    )


def create_client(base_url: str, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        event_hooks={"request": [_mark_start], "response": [_log_response]},
    )


async def fetch_post(client: httpx.AsyncClient, post_id: int) -> Post | None:
    response = await client.get(f"/posts/{post_id}")
    if response.status_code == httpx.codes.NOT_FOUND:
        return None
    response.raise_for_status()
    return to_post(ExternalPostWire.model_validate(response.json()))
