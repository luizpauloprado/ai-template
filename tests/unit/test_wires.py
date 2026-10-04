import pytest
from pydantic import ValidationError

from app.adapters.http.external_api_schemas import ExternalPostWire, to_post
from app.wires.inbound.ai import AskIn
from app.wires.inbound.items import ItemIn
from app.wires.outbound.sample import to_invoice_out
from tests.fakes import make_invoice


def test_ask_in_rejects_empty_prompt() -> None:
    with pytest.raises(ValidationError):
        AskIn(prompt="")


def test_item_in_requires_object_details() -> None:
    with pytest.raises(ValidationError):
        ItemIn.model_validate({"details": [1, 2]})


def test_external_post_wire_maps_camel_case_to_domain() -> None:
    wire = ExternalPostWire.model_validate({"id": 1, "userId": 7, "title": "t", "body": "b"})

    assert to_post(wire).user_id == 7


def test_to_invoice_out_keeps_nested_structure() -> None:
    invoice = make_invoice()

    wire_out = to_invoice_out(invoice)

    assert wire_out.model_dump() == invoice.model_dump()
    assert wire_out.items[0].code == "3065"
    assert wire_out.issuer.document == "11.222.333/0001-81"
