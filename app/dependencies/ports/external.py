from functools import partial
from typing import Annotated

from fastapi import Depends

from app.adapters.http import external_api_client
from app.dependencies.resources import HttpClientDep
from app.domain.ports import FetchPost


def get_fetch_post(client: HttpClientDep) -> FetchPost:
    return partial(external_api_client.fetch_post, client)


FetchPostDep = Annotated[FetchPost, Depends(get_fetch_post)]
