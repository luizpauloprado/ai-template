import httpx
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies import get_fetch_post
from app.domain.models import Post
from tests.fakes import fake_fetch_post


async def test_get_post(app: FastAPI, client: AsyncClient) -> None:
    post = Post(id=1, user_id=3, title="title", body="body")
    app.dependency_overrides[get_fetch_post] = lambda: fake_fetch_post({1: post})

    response = await client.get("/external/posts/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "user_id": 3, "title": "title", "body": "body"}


async def test_get_post_not_found(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_fetch_post] = lambda: fake_fetch_post({})

    assert (await client.get("/external/posts/99")).status_code == 404


async def test_upstream_error_returns_502(app: FastAPI, client: AsyncClient) -> None:
    async def broken(post_id: int) -> Post | None:
        raise httpx.ConnectError("down")

    app.dependency_overrides[get_fetch_post] = lambda: broken

    assert (await client.get("/external/posts/1")).status_code == 502
