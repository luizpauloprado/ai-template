from app.domain.models import GeneratedText, GenerationConfig
from app.domain.ports import GenerateText, GenerateTextWithConfig


async def generate(prompt: str, generate_text: GenerateText) -> GeneratedText:
    return await generate_text(prompt.strip())


async def generate_with_config(
    prompt: str,
    config: GenerationConfig,
    generate_text_with_config: GenerateTextWithConfig,
) -> GeneratedText:
    return await generate_text_with_config(prompt.strip(), config)
