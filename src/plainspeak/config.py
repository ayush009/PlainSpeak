"""Application settings loaded from environment variables and `.env`."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-5"
    anthropic_effort: str = "medium"
    anthropic_fallbacks: str = "default"

    # Ollama (local LLM — used when anthropic_api_key is empty or USE_OLLAMA=true)
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Groq (free cloud inference — https://console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenRouter (free cloud inference — https://openrouter.ai — takes priority when set)
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-70b-instruct:free"

    # Voice
    reson8_api_key: str = ""

    # Server
    port: int = 3001
    host: str = "127.0.0.1"
    app_env: str = "development"

    # CORS — comma-separated origins
    cors_origins: str = "http://localhost:3001,http://localhost:8000"

    # Storage
    plainspeak_data_dir: Path = Path("data")

    @property
    def cases_dir(self) -> Path:
        return self.plainspeak_data_dir / "cases"

    @property
    def uploads_dir(self) -> Path:
        return self.plainspeak_data_dir / "uploads"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
