from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.dependencies import get_fetch_post
from app.domain.ports import FetchPost
from app.services import external_service
from app.wires.external_out import PostOut, to_post_out

router = APIRouter(prefix="/external", tags=["external"])


@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: Annotated[int, Path(ge=1)],
    fetch_post: Annotated[FetchPost, Depends(get_fetch_post)],
) -> PostOut:
    post = await external_service.get_post(post_id, fetch_post)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    return to_post_out(post)
