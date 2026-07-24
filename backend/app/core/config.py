"""Application settings, loaded from environment / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- LLM ----
    # Which provider to use for the agent. Currently only "groq" is supported.
    llm_provider: str = "groq"

    # Groq (free tier)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ---- MongoDB ----
    mongodb_uri: str = "mongodb://root:example@localhost:27017/"
    mongodb_db: str = "procurement"
    mongodb_collection: str = "purchase_orders"

    # ---- API ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:4200"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a list (config stores them comma-separated)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
