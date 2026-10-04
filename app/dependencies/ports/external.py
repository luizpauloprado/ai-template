from functools import partial
from typing import Annotated

import httpx
from fastapi import Depends

from app.adapters.http import external_api_client
from app.dependencies.resources import get_http_client
from app.domain.ports import FetchPost


def get_fetch_post(client: Annotated[httpx.AsyncClient, Depends(get_http_client)]) -> FetchPost:
    return partial(external_api_client.fetch_post, client)
