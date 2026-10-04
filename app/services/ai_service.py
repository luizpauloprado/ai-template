from app.domain.models import GeneratedText, GenerationConfig
from app.domain.ports import Ask, AskWithConfig


async def ask(prompt: str, llm: Ask) -> GeneratedText:
    return await llm(prompt.strip())


async def ask_with_config(
    prompt: str, config: GenerationConfig, llm: AskWithConfig
) -> GeneratedText:
    return await llm(prompt.strip(), config)
