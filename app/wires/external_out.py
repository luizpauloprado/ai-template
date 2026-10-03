from pydantic import BaseModel

from app.domain.models import Post


class PostOut(BaseModel):
    id: int
    user_id: int
    title: str
    body: str


def to_post_out(post: Post) -> PostOut:
    return PostOut(id=post.id, user_id=post.user_id, title=post.title, body=post.body)
