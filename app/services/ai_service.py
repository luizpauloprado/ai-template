from app.domain.models import GeneratedText
from app.domain.ports import GenerateText


async def generate(prompt: str, generate_text: GenerateText) -> GeneratedText:
    return await generate_text(prompt.strip())
