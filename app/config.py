from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ai-template"
    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql://app:app@localhost:5432/app"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    # USD por 1M tokens, usados só para estimar custo no log (0 = não calcula)
    gemini_input_price_per_mtok: float = 0.0
    gemini_output_price_per_mtok: float = 0.0
    # Resiliência: timeout por tentativa e retry com backoff exponencial + jitter
    # (só em 408/429/5xx e erros de rede; erros 4xx do cliente não são retentados)
    gemini_timeout_seconds: float = 60.0
    gemini_retry_attempts: int = 3  # inclui a primeira chamada (1 = sem retry)
    gemini_retry_initial_delay_seconds: float = 1.0
    gemini_retry_max_delay_seconds: float = 10.0

    external_api_base_url: str = "https://jsonplaceholder.typicode.com"
    http_timeout_seconds: float = 10.0

    health_check_timeout_seconds: float = 3.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
