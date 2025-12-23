"""
Cerebras Provider
=================

Cerebras Cloud API provider - ultra-fast inference with Llama models.

Get your key: https://cloud.cerebras.ai
"""

import time
from collections.abc import AsyncIterator

import structlog
from cerebras.cloud.sdk import AsyncCerebras

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

logger = structlog.get_logger()


# Cerebras available models
CEREBRAS_MODELS = {
    "llama-3.3-70b": "Llama 3.3 70B - Best for code",
    "llama-3.1-70b": "Llama 3.1 70B - Previous gen",
    "llama-3.1-8b": "Llama 3.1 8B - Fast",
}


class CerebrasProvider(LLMProvider):
    """
    Cerebras Cloud API provider.

    Features:
    - Ultra-fast inference (comparable to Groq)
    - Native JSON mode
    - Streaming support
    - Llama model variants
    """

    name = "cerebras"
    supports_json_mode = True
    supports_streaming = True

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = AsyncCerebras(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion using Cerebras."""
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            provider=self.name,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            finish_reason=response.choices[0].finish_reason,
            latency_ms=latency_ms,
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate JSON completion using Cerebras."""
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            response_format={"type": "json_object"},
        )

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            provider=self.name,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            finish_reason=response.choices[0].finish_reason,
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion using Cerebras."""
        stream = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
