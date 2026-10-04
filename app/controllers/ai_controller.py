from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_generate_text
from app.domain.ports import GenerateText
from app.services import ai_service
from app.wires.inbound.ai import GenerateIn
from app.wires.outbound.ai import GenerateOut, to_generate_out

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=GenerateOut)
async def generate(
    wire_in: GenerateIn,
    generate_text: Annotated[GenerateText, Depends(get_generate_text)],
) -> GenerateOut:
    generated = await ai_service.generate(wire_in.prompt, generate_text)
    return to_generate_out(generated)
