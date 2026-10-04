"""Extração de dados da NF-e de exemplo que acompanha o projeto."""

from pathlib import Path

from app.domain.models import Invoice
from app.domain.ports import ExtractInvoice, ReadFile

SAMPLE_INVOICE_PATH = Path(__file__).parent / "invoice_sample.pdf"

EXTRACT_INVOICE_PROMPT = """\
Você recebe a DANFE de uma Nota Fiscal Eletrônica (NF-e) brasileira em PDF.
Extraia os dados da nota exatamente como aparecem no documento:
- number e series como texto, mantendo a formatação (ex.: "000.001.234", "001");
- access_key com os 44 dígitos da chave de acesso, como aparece no documento;
- issue_date no formato YYYY-MM-DD;
- issuer é o emitente da nota e recipient é o destinatário;
- document é o CNPJ ou CPF com a pontuação do documento;
- valores monetários e quantidades como números com ponto decimal (ex.: 59.98);
- additional_info com o texto de "Dados adicionais";
- campos ausentes ou vazios devem ser null. Não invente dados.
"""


async def extract_sample_invoice(read: ReadFile, extract: ExtractInvoice) -> Invoice:
    pdf = await read(SAMPLE_INVOICE_PATH)
    return await extract(pdf, EXTRACT_INVOICE_PROMPT)
