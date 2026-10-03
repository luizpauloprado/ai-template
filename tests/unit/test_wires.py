import pytest
from pydantic import ValidationError

from app.adapters.http.external_api_wires import ExternalPostWire, to_post
from app.wires.ai_in import GenerateIn
from app.wires.items_in import ItemIn


def test_generate_in_rejects_empty_prompt() -> None:
    with pytest.raises(ValidationError):
        GenerateIn(prompt="")


def test_item_in_requires_object_details() -> None:
    with pytest.raises(ValidationError):
        ItemIn.model_validate({"details": [1, 2]})


def test_external_post_wire_maps_camel_case_to_domain() -> None:
    wire = ExternalPostWire.model_validate({"id": 1, "userId": 7, "title": "t", "body": "b"})

    assert to_post(wire).user_id == 7
