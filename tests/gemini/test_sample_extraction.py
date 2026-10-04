from functools import partial

import pytest
from google import genai

from app.adapters.ai import gemini_adapter
from app.adapters.fs import file_reader
from app.config import get_settings
from app.services import sample_service

pytestmark = pytest.mark.gemini


async def test_extracts_sample_invoice_with_real_gemini(gemini_client: genai.Client) -> None:
    settings = get_settings()
    pricing = gemini_adapter.GeminiPricing(
        input_per_mtok=settings.gemini_input_price_per_mtok,
        output_per_mtok=settings.gemini_output_price_per_mtok,
    )
    extract = partial(
        gemini_adapter.extract_invoice, gemini_client, settings.gemini_model, pricing
    )

    invoice = await sample_service.extract_sample_invoice(file_reader.read_bytes, extract)

    assert invoice.number == "000.001.234"
    assert invoice.series == "001"
    assert invoice.access_key.replace(" ", "") == "41260911222333000181550010000012341123456784"
    assert invoice.issue_date == "2026-09-29"
    assert invoice.issuer.name == "EMPRESA EXEMPLO LTDA"
    assert invoice.issuer.document == "11.222.333/0001-81"
    assert invoice.recipient.name == "Maria Souza Oliveira"
    assert invoice.recipient.document == "123.456.789-09"
    assert len(invoice.items) == 1
    assert invoice.items[0].code == "3065"
    assert invoice.items[0].quantity == 2
    assert invoice.items[0].unit_price == pytest.approx(29.99)
    assert invoice.totals.invoice_total == pytest.approx(59.98)
