import httpx
import pytest
from fastapi import FastAPI
from google.genai import errors as genai_errors
from httpx import AsyncClient

from app.dependencies import get_ask, get_ask_with_config
from app.domain.models import GeneratedText, GenerationConfig
from app.domain.ports import Ask
from tests.fakes import fake_ask, fake_ask_with_config


async def test_ask(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_ask] = lambda: fake_ask("gemini-fake")

    response = await client.post("/ai/ask", json={"prompt": "hi"})

    assert response.status_code == 200
    assert response.json() == {"text": "echo: hi", "model": "gemini-fake"}


async def test_ask_rejects_empty_prompt(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_ask] = lambda: fake_ask()

    response = await client.post("/ai/ask", json={"prompt": ""})

    assert response.status_code == 422


async def test_ask_without_api_key_returns_503(client: AsyncClient) -> None:
    response = await client.post("/ai/ask", json={"prompt": "hi"})

    assert response.status_code == 503


async def test_ask_with_config(app: FastAPI, client: AsyncClient) -> None:
    calls: list[tuple[str, GenerationConfig]] = []
    app.dependency_overrides[get_ask_with_config] = lambda: fake_ask_with_config(
        calls, "gemini-fake"
    )

    response = await client.post(
        "/ai/ask/advanced",
        json={"prompt": "hi", "system_instruction": "seja breve", "temperature": 0.2},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "echo: hi", "model": "gemini-fake"}
    assert calls == [("hi", GenerationConfig(system_instruction="seja breve", temperature=0.2))]


async def test_ask_with_config_rejects_invalid_temperature(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_ask_with_config] = lambda: fake_ask_with_config()

    response = await client.post("/ai/ask/advanced", json={"prompt": "hi", "temperature": 3})

    assert response.status_code == 422


async def test_ask_with_config_without_api_key_returns_503(client: AsyncClient) -> None:
    response = await client.post("/ai/ask/advanced", json={"prompt": "hi"})

    assert response.status_code == 503


def failing_ask(exc: Exception) -> Ask:
    async def ask(prompt: str) -> GeneratedText:
        raise exc

    return ask


def api_error(cls: type[genai_errors.APIError], code: int) -> genai_errors.APIError:
    return cls(code, {"error": {"code": code, "message": "boom", "status": "X"}})


@pytest.mark.parametrize(
    "exc",
    [api_error(genai_errors.ServerError, 503), api_error(genai_errors.ClientError, 429)],
)
async def test_ask_provider_unavailable_returns_503_with_retry_after(
    app: FastAPI, client: AsyncClient, exc: Exception
) -> None:
    app.dependency_overrides[get_ask] = lambda: failing_ask(exc)

    response = await client.post("/ai/ask", json={"prompt": "hi"})

    assert response.status_code == 503
    assert int(response.headers["retry-after"]) >= 1
    assert response.json()["request_id"] == response.headers["x-request-id"]


async def test_ask_client_error_returns_502(app: FastAPI, client: AsyncClient) -> None:
    exc = api_error(genai_errors.ClientError, 400)
    app.dependency_overrides[get_ask] = lambda: failing_ask(exc)

    response = await client.post("/ai/ask", json={"prompt": "hi"})

    assert response.status_code == 502
    assert "retry-after" not in response.headers


async def test_ask_timeout_returns_504(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_ask] = lambda: failing_ask(httpx.ReadTimeout("slow"))

    response = await client.post("/ai/ask", json={"prompt": "hi"})

    assert response.status_code == 504
