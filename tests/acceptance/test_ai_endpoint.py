from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies import get_generate_text
from tests.fakes import fake_generate_text


async def test_generate(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_generate_text] = lambda: fake_generate_text("gemini-fake")

    response = await client.post("/ai/generate", json={"prompt": "hi"})

    assert response.status_code == 200
    assert response.json() == {"text": "echo: hi", "model": "gemini-fake"}


async def test_generate_rejects_empty_prompt(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_generate_text] = lambda: fake_generate_text()

    response = await client.post("/ai/generate", json={"prompt": ""})

    assert response.status_code == 422


async def test_generate_without_api_key_returns_503(client: AsyncClient) -> None:
    response = await client.post("/ai/generate", json={"prompt": "hi"})

    assert response.status_code == 503
