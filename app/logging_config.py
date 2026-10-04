"""Logs no console (stdout), com o request_id de cada requisição em todas as linhas."""

import logging
import logging.config
from contextvars import ContextVar

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s"

# Preenchido pelo middleware em app/main.py; "-" fora de uma requisição (startup, etc.).
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def add_request_id(record: logging.LogRecord) -> bool:
    record.request_id = request_id_var.get()
    return True


def configure_logging(level: str) -> None:
    level = level.upper()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": lambda: add_request_id}},
            "formatters": {"console": {"format": LOG_FORMAT}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "console",
                    "filters": ["request_id"],
                }
            },
            "loggers": {
                # propagate=True mantém os logs visíveis para o caplog nos testes
                "app": {"handlers": ["console"], "level": level, "propagate": True},
                "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.error": {"level": level},
                # o middleware de app/main.py já loga cada request (com duração e request_id)
                "uvicorn.access": {"level": "WARNING"},
                # avisos do SDK do Gemini no mesmo formato (sem isso saem crus no stderr)
                "google_genai": {"handlers": ["console"], "level": "WARNING", "propagate": False},
                # cada retry do SDK (503/429/timeout) é logado em INFO por este logger
                "google_genai._api_client": {"level": "INFO"},
            },
        }
    )
