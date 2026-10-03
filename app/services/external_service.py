from app.domain.models import Post
from app.domain.ports import FetchPost


async def get_post(post_id: int, fetch_post: FetchPost) -> Post | None:
    return await fetch_post(post_id)
