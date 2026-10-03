from pydantic import BaseModel

from app.domain.models import GeneratedText


class GenerateOut(BaseModel):
    text: str
    model: str


def to_generate_out(generated: GeneratedText) -> GenerateOut:
    return GenerateOut(text=generated.text, model=generated.model)
