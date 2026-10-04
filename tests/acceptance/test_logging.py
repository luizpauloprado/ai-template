import logging

import pytest
from fastapi import FastAPI
from google.genai import errors as genai_errors
from httpx import AsyncClient

from app.dependencies import get_extract_invoice, get_read_file
from app.domain.models import Invoice
from app.services.sample_service import SAMPLE_INVOICE_PATH
from tests.fakes import fake_read_file


def request_logs(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "app.main"]


async def test_response_has_generated_request_id(client: AsyncClient) -> None:
    response = await client.get("/items")

    assert len(response.headers["x-request-id"]) == 12


async def test_incoming_request_id_is_reused(client: AsyncClient) -> None:
    response = await client.get("/items", headers={"X-Request-ID": "from-client"})

    assert response.headers["x-request-id"] == "from-client"


async def test_request_is_logged(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app")

    await client.get("/items")

    [record] = request_logs(caplog)
    assert record.levelname == "INFO"
    assert record.getMessage().startswith("GET /items -> 200 (")


async def test_not_found_is_logged_as_warning(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    await client.get("/items/999")

    [record] = request_logs(caplog)
    assert record.levelname == "WARNING"
    assert "-> 404" in record.getMessage()


async def test_upstream_error_is_logged_with_details(
    app: FastAPI, client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    async def broken(pdf: bytes, prompt: str) -> Invoice:
        raise genai_errors.ClientError(404, {"error": {"message": "model no longer available"}})

    app.dependency_overrides[get_read_file] = lambda: fake_read_file({SAMPLE_INVOICE_PATH: b"%PDF"})
    app.dependency_overrides[get_extract_invoice] = lambda: broken

    response = await client.get("/sample/extract-invoice", headers={"X-Request-ID": "req-1"})

    assert response.status_code == 502
    assert response.json() == {"detail": "upstream error: ClientError", "request_id": "req-1"}
    upstream, request = request_logs(caplog)
    assert upstream.levelname == "ERROR"
    assert "model no longer available" in upstream.getMessage()
    assert upstream.exc_info is not None
    assert request.getMessage().startswith("GET /sample/extract-invoice -> 502")
