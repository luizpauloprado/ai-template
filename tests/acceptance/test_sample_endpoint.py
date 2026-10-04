from fastapi import FastAPI
from google.genai import errors as genai_errors
from httpx import AsyncClient

from app.dependencies import get_extract_invoice, get_read_file
from app.domain.models import Invoice
from app.services.sample_service import SAMPLE_INVOICE_PATH
from tests.fakes import fake_extract_invoice, fake_read_file, make_invoice


async def test_get_sample_returns_extracted_invoice(app: FastAPI, client: AsyncClient) -> None:
    invoice = make_invoice()
    calls: list[tuple[bytes, str]] = []
    app.dependency_overrides[get_read_file] = lambda: fake_read_file({SAMPLE_INVOICE_PATH: b"%PDF"})
    app.dependency_overrides[get_extract_invoice] = lambda: fake_extract_invoice(invoice, calls)

    response = await client.get("/sample/extract-invoice")

    assert response.status_code == 200
    assert response.json() == invoice.model_dump(mode="json")
    assert [pdf for pdf, _ in calls] == [b"%PDF"]


async def test_get_sample_reads_real_pdf_from_project(app: FastAPI, client: AsyncClient) -> None:
    calls: list[tuple[bytes, str]] = []
    app.dependency_overrides[get_extract_invoice] = lambda: fake_extract_invoice(
        make_invoice(), calls
    )

    response = await client.get("/sample/extract-invoice")

    assert response.status_code == 200
    assert calls[0][0] == SAMPLE_INVOICE_PATH.read_bytes()


async def test_get_sample_without_api_key_returns_503(client: AsyncClient) -> None:
    response = await client.get("/sample/extract-invoice")

    assert response.status_code == 503


async def test_get_sample_provider_down_returns_503(app: FastAPI, client: AsyncClient) -> None:
    async def broken(pdf: bytes, prompt: str) -> Invoice:
        raise genai_errors.ServerError(500, {"error": {"message": "down"}})

    app.dependency_overrides[get_extract_invoice] = lambda: broken

    assert (await client.get("/sample/extract-invoice")).status_code == 503


async def test_get_sample_client_error_returns_502(app: FastAPI, client: AsyncClient) -> None:
    async def broken(pdf: bytes, prompt: str) -> Invoice:
        raise genai_errors.ClientError(400, {"error": {"message": "bad"}})

    app.dependency_overrides[get_extract_invoice] = lambda: broken

    assert (await client.get("/sample/extract-invoice")).status_code == 502


async def test_sample_root_is_not_routed(client: AsyncClient) -> None:
    assert (await client.get("/sample")).status_code == 404
