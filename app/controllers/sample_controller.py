from fastapi import APIRouter

from app.dependencies import ExtractInvoiceDep, ReadFileDep
from app.services import sample_service
from app.wires.outbound.sample import InvoiceOut, to_invoice_out

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("/extract-invoice", response_model=InvoiceOut)
async def extract_sample_invoice(read: ReadFileDep, extract: ExtractInvoiceDep) -> InvoiceOut:
    invoice = await sample_service.extract_sample_invoice(read, extract)
    return to_invoice_out(invoice)
