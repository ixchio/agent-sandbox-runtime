"""Provider base classes and types."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class ProviderConfig:
    """LLM provider configuration."""

    api_key: str
    model: str
    base_url: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    temperature: float = 0.2
    max_tokens: int = 4096
    extra: dict[str, Any] = field(default_factory=dict)


class LLMResponse(BaseModel):
    """Standardized LLM response."""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str | None = None
    latency_ms: float = 0.0
    raw: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    name: str = "base"
    supports_json_mode: bool = True
    supports_streaming: bool = True

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion."""
        pass

    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate JSON output."""
        pass

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass

    async def health_check(self) -> bool:
        """Check provider availability."""
        try:
            resp = await self.generate("You are helpful.", "Say ok.", max_tokens=10)
            return bool(resp.content)
        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "provider": self.name,
            "model": self.config.model,
            "json_mode": self.supports_json_mode,
            "streaming": self.supports_streaming,
        }
