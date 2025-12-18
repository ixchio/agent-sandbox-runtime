"""Provider factory."""

from typing import Literal

import structlog

from agent_sandbox.providers.base import LLMProvider, ProviderConfig

log = structlog.get_logger()

ProviderType = Literal["groq", "openrouter", "anthropic", "google", "ollama", "openai"]

DEFAULTS = {
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "anthropic": "claude-3-5-sonnet-20241022",
    "google": "gemini-1.5-flash",
    "ollama": "qwen2.5-coder:7b",
    "openai": "gpt-4o-mini",
}


def create_provider(
    provider_type: ProviderType,
    api_key: str,
    model: str | None = None,
    base_url: str | None = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider instance."""

    # Late imports to avoid circular deps
    if provider_type == "groq":
        from agent_sandbox.providers.groq import GroqProvider as Cls
    elif provider_type == "openrouter":
        from agent_sandbox.providers.openrouter import OpenRouterProvider as Cls
    elif provider_type == "anthropic":
        from agent_sandbox.providers.anthropic import AnthropicProvider as Cls
    elif provider_type == "google":
        from agent_sandbox.providers.google import GoogleProvider as Cls
    elif provider_type == "ollama":
        from agent_sandbox.providers.ollama import OllamaProvider as Cls
    elif provider_type == "openai":
        from agent_sandbox.providers.openai import OpenAIProvider as Cls
    else:
        raise ValueError(f"Unknown provider: {provider_type}")

    config = ProviderConfig(
        api_key=api_key,
        model=model or DEFAULTS.get(provider_type, ""),
        base_url=base_url,
        **kwargs,
    )

    log.info("Creating LLM provider", provider=provider_type, model=config.model)
    return Cls(config)


def get_available_providers() -> list[str]:
    """List available providers."""
    return list(DEFAULTS.keys())
