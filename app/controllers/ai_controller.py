from fastapi import APIRouter

from app.dependencies import AskDep, AskWithConfigDep
from app.services import ai_service
from app.wires.inbound.ai import AskIn, AskWithConfigIn, to_generation_config
from app.wires.outbound.ai import AskOut, to_ask_out

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=AskOut)
async def ask(wire_in: AskIn, llm: AskDep) -> AskOut:
    generated = await ai_service.ask(wire_in.prompt, llm)
    return to_ask_out(generated)


@router.post("/ask/advanced", response_model=AskOut)
async def ask_with_config(wire_in: AskWithConfigIn, llm: AskWithConfigDep) -> AskOut:
    generated = await ai_service.ask_with_config(wire_in.prompt, to_generation_config(wire_in), llm)
    return to_ask_out(generated)
