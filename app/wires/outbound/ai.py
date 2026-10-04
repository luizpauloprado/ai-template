from pydantic import BaseModel

from app.domain.models import GeneratedText


class AskOut(BaseModel):
    text: str
    model: str


def to_ask_out(generated: GeneratedText) -> AskOut:
    return AskOut(text=generated.text, model=generated.model)
