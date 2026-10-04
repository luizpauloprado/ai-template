from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies import get_generate_text, get_generate_text_with_config
from app.domain.models import GenerationConfig
from tests.fakes import fake_generate_text, fake_generate_text_with_config


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


async def test_generate_advanced(app: FastAPI, client: AsyncClient) -> None:
    calls: list[tuple[str, GenerationConfig]] = []
    app.dependency_overrides[get_generate_text_with_config] = lambda: (
        fake_generate_text_with_config(calls, "gemini-fake")
    )

    response = await client.post(
        "/ai/generate/advanced",
        json={"prompt": "hi", "system_instruction": "seja breve", "temperature": 0.2},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "echo: hi", "model": "gemini-fake"}
    assert calls == [("hi", GenerationConfig(system_instruction="seja breve", temperature=0.2))]


async def test_generate_advanced_rejects_invalid_temperature(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_generate_text_with_config] = lambda: (
        fake_generate_text_with_config()
    )

    response = await client.post("/ai/generate/advanced", json={"prompt": "hi", "temperature": 3})

    assert response.status_code == 422


async def test_generate_advanced_without_api_key_returns_503(client: AsyncClient) -> None:
    response = await client.post("/ai/generate/advanced", json={"prompt": "hi"})

    assert response.status_code == 503
