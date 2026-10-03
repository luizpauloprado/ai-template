from app.services import ai_service
from tests.fakes import fake_generate_text


async def test_generate_strips_prompt() -> None:
    generated = await ai_service.generate("  hello  ", fake_generate_text())

    assert generated.text == "echo: hello"
    assert generated.model == "fake-model"
