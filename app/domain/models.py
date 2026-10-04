"""Entidades de domínio. Não conhecem HTTP, banco nem SDKs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ComponentState = Literal["up", "down"]
OverallState = Literal["ok", "degraded"]


class ComponentStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ComponentState
    version: str | None = None
    detail: str | None = None


class HealthStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: OverallState
    components: dict[str, ComponentStatus]


class Item(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    details: dict[str, Any]
    updated_at: datetime


class Post(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    user_id: int
    title: str
    body: str


class GeneratedText(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model: str


class GenerationConfig(BaseModel):
    """Parâmetros opcionais de geração. Só o que for informado é enviado ao provedor."""

    model_config = ConfigDict(frozen=True)

    system_instruction: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    max_output_tokens: int | None = None
    stop_sequences: list[str] | None = None
    seed: int | None = None


class InvoiceParty(BaseModel):
    """Emitente ou destinatário de uma NF-e."""

    model_config = ConfigDict(frozen=True)

    name: str
    document: str  # CNPJ ou CPF
    state_registration: str | None
    address: str | None
    district: str | None
    city: str | None
    state: str | None
    zip_code: str | None


class InvoiceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    description: str
    ncm: str | None
    cfop: str | None
    unit: str | None
    quantity: float
    unit_price: float
    total: float


class InvoiceTotals(BaseModel):
    model_config = ConfigDict(frozen=True)

    icms_base: float
    icms: float
    products_total: float
    freight: float
    insurance: float
    discount: float
    other_expenses: float
    ipi: float
    invoice_total: float


class Invoice(BaseModel):
    """Dados extraídos de uma DANFE (NF-e)."""

    model_config = ConfigDict(frozen=True)

    number: str
    series: str
    access_key: str
    issue_date: str  # YYYY-MM-DD
    operation_nature: str | None
    authorization_protocol: str | None
    issuer: InvoiceParty
    recipient: InvoiceParty
    items: list[InvoiceItem]
    totals: InvoiceTotals
    additional_info: str | None
