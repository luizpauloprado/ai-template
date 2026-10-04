from app.services import sample_service
from app.services.sample_service import EXTRACT_INVOICE_PROMPT, SAMPLE_INVOICE_PATH
from tests.fakes import fake_extract_invoice, fake_read_file, make_invoice


async def test_extract_sample_invoice_sends_sample_pdf_and_prompt() -> None:
    calls: list[tuple[bytes, str]] = []
    invoice = make_invoice()
    read = fake_read_file({SAMPLE_INVOICE_PATH: b"%PDF-fake"})

    extracted = await sample_service.extract_sample_invoice(
        read, fake_extract_invoice(invoice, calls)
    )

    assert extracted == invoice
    assert calls == [(b"%PDF-fake", EXTRACT_INVOICE_PROMPT)]


def test_sample_invoice_pdf_ships_with_the_service() -> None:
    assert SAMPLE_INVOICE_PATH.parent.name == "services"
    assert SAMPLE_INVOICE_PATH.read_bytes().startswith(b"%PDF")
