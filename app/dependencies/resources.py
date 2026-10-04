"""Recursos que vivem em `app.state` (criados no lifespan)."""

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from google import genai
from psycopg_pool import AsyncConnectionPool


def get_db_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.db_pool


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_gemini_client(request: Request) -> genai.Client:
    client: genai.Client | None = getattr(request.app.state, "gemini_client", None)
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "GEMINI_API_KEY não configurada")
    return client


PoolDep = Annotated[AsyncConnectionPool, Depends(get_db_pool)]
GeminiClientDep = Annotated[genai.Client, Depends(get_gemini_client)]
