"""Wires da API externa (JSONPlaceholder): formato que chega pela rede.

Ficam dentro do adapter porque são detalhe de infraestrutura; o resto da
aplicação só enxerga o modelo de domínio `Post`.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Post


class ExternalPostWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    user_id: int = Field(alias="userId")
    title: str
    body: str


def to_post(wire: ExternalPostWire) -> Post:
    return Post(id=wire.id, user_id=wire.user_id, title=wire.title, body=wire.body)
