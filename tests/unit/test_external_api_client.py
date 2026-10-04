import logging

import httpx
import pytest
import respx

from app.adapters.http.external_api_client import create_client, fetch_post

BASE_URL = "https://api.test"


@respx.mock
async def test_fetch_post_returns_domain_post() -> None:
    respx.get(f"{BASE_URL}/posts/1").respond(json={"id": 1, "userId": 2, "title": "t", "body": "b"})
    async with create_client(BASE_URL, timeout=1) as client:
        post = await fetch_post(client, 1)

    assert post is not None
    assert post.user_id == 2


@respx.mock
async def test_fetch_post_404_returns_none() -> None:
    respx.get(f"{BASE_URL}/posts/999").respond(status_code=404)
    async with create_client(BASE_URL, timeout=1) as client:
        assert await fetch_post(client, 999) is None


@respx.mock
async def test_fetch_post_500_raises() -> None:
    respx.get(f"{BASE_URL}/posts/1").respond(status_code=500)
    async with create_client(BASE_URL, timeout=1) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_post(client, 1)


@respx.mock
async def test_requests_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app")
    respx.get(f"{BASE_URL}/posts/999").respond(status_code=404)
    async with create_client(BASE_URL, timeout=1) as client:
        await fetch_post(client, 999)

    messages = [r.getMessage() for r in caplog.records if r.name.startswith("app.adapters.http")]
    assert len(messages) == 1
    assert messages[0].startswith(f"http GET {BASE_URL}/posts/999 -> 404")
