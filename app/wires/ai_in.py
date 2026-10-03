from pydantic import BaseModel, Field


class GenerateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
