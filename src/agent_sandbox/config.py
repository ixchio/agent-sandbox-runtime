"""Config management with multi-provider support."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderType = Literal["groq", "openrouter", "anthropic", "google", "ollama", "openai"]


class Settings(BaseSettings):
    """App settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider
    llm_provider: ProviderType = "groq"

    # API Keys
    groq_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Models
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    google_model: str = "gemini-1.5-flash"
    ollama_model: str = "qwen2.5-coder:7b"
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"

    # Sandbox
    sandbox_timeout_seconds: float = Field(default=5.0, ge=1.0, le=60.0)
    sandbox_memory_limit_mb: int = Field(default=256, ge=64, le=2048)
    sandbox_cpu_limit: float = Field(default=0.5, ge=0.1, le=4.0)
    sandbox_network_enabled: bool = False
    sandbox_pool_size: int = Field(default=5, ge=1, le=20)
    sandbox_image: str = "agent-sandbox-python:latest"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_debug: bool = False

    # Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "agent_memory"
    redis_url: str = "redis://localhost:6379/0"

    # Agent
    max_reflexion_attempts: int = Field(default=3, ge=1, le=10)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"

    def get_provider_api_key(self) -> str:
        """Get API key for active provider."""
        keys = {
            "groq": self.groq_api_key,
            "openrouter": self.openrouter_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
            "ollama": None,
            "openai": self.openai_api_key,
        }
        key = keys.get(self.llm_provider)
        if key is None and self.llm_provider != "ollama":
            raise ValueError(f"No API key for {self.llm_provider}")
        return key.get_secret_value() if key else ""

    def get_provider_model(self) -> str:
        """Get model for active provider."""
        models = {
            "groq": self.groq_model,
            "openrouter": self.openrouter_model,
            "anthropic": self.anthropic_model,
            "google": self.google_model,
            "ollama": self.ollama_model,
            "openai": self.openai_model,
        }
        return models.get(self.llm_provider, "")

    def get_provider_base_url(self) -> str | None:
        """Get base URL for active provider."""
        if self.llm_provider == "ollama":
            return self.ollama_base_url
        return None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
