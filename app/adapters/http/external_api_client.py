"""Adapter HTTP para a API externa."""

import httpx

from app.adapters.http.external_api_wires import ExternalPostWire, to_post
from app.domain.models import Post


def create_client(base_url: str, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)


async def fetch_post(client: httpx.AsyncClient, post_id: int) -> Post | None:
    response = await client.get(f"/posts/{post_id}")
    if response.status_code == httpx.codes.NOT_FOUND:
        return None
    response.raise_for_status()
    return to_post(ExternalPostWire.model_validate(response.json()))
