from pydantic import BaseModel, Field

from app.domain.models import GenerationConfig


class GenerateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


class GenerateWithConfigIn(GenerateIn):
    system_instruction: str | None = Field(default=None, max_length=8000)
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    top_k: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    stop_sequences: list[str] | None = Field(default=None, max_length=5)
    seed: int | None = None


def to_generation_config(wire_in: GenerateWithConfigIn) -> GenerationConfig:
    return GenerationConfig(**wire_in.model_dump(exclude={"prompt"}))
