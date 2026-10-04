from pydantic import BaseModel

from app.domain.models import Invoice


class InvoicePartyOut(BaseModel):
    name: str
    document: str
    state_registration: str | None
    address: str | None
    district: str | None
    city: str | None
    state: str | None
    zip_code: str | None


class InvoiceItemOut(BaseModel):
    code: str
    description: str
    ncm: str | None
    cfop: str | None
    unit: str | None
    quantity: float
    unit_price: float
    total: float


class InvoiceTotalsOut(BaseModel):
    icms_base: float
    icms: float
    products_total: float
    freight: float
    insurance: float
    discount: float
    other_expenses: float
    ipi: float
    invoice_total: float


class InvoiceOut(BaseModel):
    number: str
    series: str
    access_key: str
    issue_date: str
    operation_nature: str | None
    authorization_protocol: str | None
    issuer: InvoicePartyOut
    recipient: InvoicePartyOut
    items: list[InvoiceItemOut]
    totals: InvoiceTotalsOut
    additional_info: str | None


def to_invoice_out(invoice: Invoice) -> InvoiceOut:
    return InvoiceOut.model_validate(invoice.model_dump())
