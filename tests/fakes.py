"""Fakes dos ports: funções simples, sem banco nem rede."""

from datetime import UTC, datetime
from itertools import count
from pathlib import Path
from typing import Any

from app.domain.models import (
    ComponentStatus,
    GeneratedText,
    GenerationConfig,
    Invoice,
    InvoiceItem,
    InvoiceParty,
    InvoiceTotals,
    Item,
    Post,
)
from app.domain.ports import (
    Ask,
    AskWithConfig,
    CheckComponent,
    ExtractInvoice,
    FetchPost,
    ReadFile,
)


def make_fake_item_table() -> dict[str, Any]:
    """Simula a tabela `item` com um dict. Retorna as funções que implementam os ports."""
    rows: dict[int, Item] = {}
    ids = count(1)

    async def insert(details: dict[str, Any]) -> Item:
        item = Item(id=next(ids), details=details, updated_at=datetime.now(UTC))
        rows[item.id] = item
        return item

    async def get(item_id: int) -> Item | None:
        return rows.get(item_id)

    async def list_all(limit: int, offset: int) -> list[Item]:
        return [rows[key] for key in sorted(rows)][offset : offset + limit]

    async def update(item_id: int, details: dict[str, Any]) -> Item | None:
        if item_id not in rows:
            return None
        rows[item_id] = Item(id=item_id, details=details, updated_at=datetime.now(UTC))
        return rows[item_id]

    async def delete(item_id: int) -> bool:
        return rows.pop(item_id, None) is not None

    return {"insert": insert, "get": get, "list": list_all, "update": update, "delete": delete}


def fake_check(status: ComponentStatus) -> CheckComponent:
    async def check() -> ComponentStatus:
        return status

    return check


def failing_check(exc: Exception) -> CheckComponent:
    async def check() -> ComponentStatus:
        raise exc

    return check


def fake_ask(model: str = "fake-model") -> Ask:
    async def ask(prompt: str) -> GeneratedText:
        return GeneratedText(text=f"echo: {prompt}", model=model)

    return ask


def fake_ask_with_config(
    calls: list[tuple[str, GenerationConfig]] | None = None, model: str = "fake-model"
) -> AskWithConfig:
    """Registra as chamadas em `calls` para os testes conferirem o que foi repassado."""

    async def ask_with_config(prompt: str, config: GenerationConfig) -> GeneratedText:
        if calls is not None:
            calls.append((prompt, config))
        return GeneratedText(text=f"echo: {prompt}", model=model)

    return ask_with_config


def fake_fetch_post(posts: dict[int, Post]) -> FetchPost:
    async def fetch_post(post_id: int) -> Post | None:
        return posts.get(post_id)

    return fetch_post


def fake_read_file(files: dict[Path, bytes]) -> ReadFile:
    """Simula o sistema de arquivos. Path desconhecido levanta `FileNotFoundError`."""

    async def read_file(path: Path) -> bytes:
        if path not in files:
            raise FileNotFoundError(path)
        return files[path]

    return read_file


def fake_extract_invoice(
    invoice: Invoice, calls: list[tuple[bytes, str]] | None = None
) -> ExtractInvoice:
    """Registra as chamadas em `calls` para os testes conferirem o que foi repassado."""

    async def extract_invoice(pdf: bytes, prompt: str) -> Invoice:
        if calls is not None:
            calls.append((pdf, prompt))
        return invoice

    return extract_invoice


def make_invoice() -> Invoice:
    """NF-e com os dados de `app/services/invoice_sample.pdf`."""
    party = {"state_registration": None, "district": "Centro", "city": "Sao Paulo", "state": "SP"}
    return Invoice(
        number="000.001.234",
        series="001",
        access_key="4126 0911 2223 3300 0181 5500 1000 0012 3411 2345 6784",
        issue_date="2026-09-29",
        operation_nature="(NF-e) Venda de mercadorias de terceiros para consumidor fin",
        authorization_protocol="141260000123 29/09/2026 11:04:41",
        issuer=InvoiceParty(
            name="EMPRESA EXEMPLO LTDA",
            document="11.222.333/0001-81",
            state_registration="1234567890",
            address="Rua das Flores, 100, SALA 2",
            district="Centro",
            city="Curitiba",
            state="PR",
            zip_code="80010000",
        ),
        recipient=InvoiceParty(
            name="Maria Souza Oliveira",
            document="123.456.789-09",
            address="Rua das Palmeiras, 123",
            zip_code="01001000",
            **party,
        ),
        items=[
            InvoiceItem(
                code="3065",
                description="CACHEPOT POTE 17 - Calcario",
                ncm="39249000",
                cfop="6108",
                unit="UN",
                quantity=2,
                unit_price=29.99,
                total=59.98,
            )
        ],
        totals=InvoiceTotals(
            icms_base=0,
            icms=0,
            products_total=59.98,
            freight=0,
            insurance=0,
            discount=0,
            other_expenses=0,
            ipi=0,
            invoice_total=59.98,
        ),
        additional_info="Documento emitido por ME ou EPP optante pelo Simples Nacional.",
    )
