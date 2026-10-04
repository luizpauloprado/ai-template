from app.domain.models import GenerationConfig
from app.services import ai_service
from tests.fakes import fake_generate_text, fake_generate_text_with_config


async def test_generate_strips_prompt() -> None:
    generated = await ai_service.generate("  hello  ", fake_generate_text())

    assert generated.text == "echo: hello"
    assert generated.model == "fake-model"


async def test_generate_with_config_strips_prompt_and_forwards_config() -> None:
    calls: list[tuple[str, GenerationConfig]] = []
    config = GenerationConfig(temperature=0.2, system_instruction="seja breve")

    generated = await ai_service.generate_with_config(
        "  hello  ", config, fake_generate_text_with_config(calls)
    )

    assert generated.text == "echo: hello"
    assert calls == [("hello", config)]
