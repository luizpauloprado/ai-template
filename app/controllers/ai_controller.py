from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_generate_text, get_generate_text_with_config
from app.domain.ports import GenerateText, GenerateTextWithConfig
from app.services import ai_service
from app.wires.inbound.ai import GenerateIn, GenerateWithConfigIn, to_generation_config
from app.wires.outbound.ai import GenerateOut, to_generate_out

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=GenerateOut)
async def generate(
    wire_in: GenerateIn,
    generate_text: Annotated[GenerateText, Depends(get_generate_text)],
) -> GenerateOut:
    generated = await ai_service.generate(wire_in.prompt, generate_text)
    return to_generate_out(generated)


@router.post("/generate/advanced", response_model=GenerateOut)
async def generate_advanced(
    wire_in: GenerateWithConfigIn,
    generate_text_with_config: Annotated[
        GenerateTextWithConfig, Depends(get_generate_text_with_config)
    ],
) -> GenerateOut:
    generated = await ai_service.generate_with_config(
        wire_in.prompt, to_generation_config(wire_in), generate_text_with_config
    )
    return to_generate_out(generated)
