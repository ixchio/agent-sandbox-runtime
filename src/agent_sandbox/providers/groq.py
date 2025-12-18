"""Groq provider - ultra fast inference."""

import time
from collections.abc import AsyncIterator

import structlog
from groq import AsyncGroq

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

log = structlog.get_logger()

MODELS = {
    "llama-3.3-70b-versatile": "Best for code",
    "llama-3.1-8b-instant": "Fastest",
    "mixtral-8x7b-32768": "Good balance",
}


class GroqProvider(LLMProvider):
    """Groq API - 100+ tokens/sec inference."""

    name = "groq"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = AsyncGroq(
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
        t0 = time.time()

        resp = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            provider=self.name,
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            total_tokens=resp.usage.total_tokens if resp.usage else 0,
            finish_reason=resp.choices[0].finish_reason,
            latency_ms=(time.time() - t0) * 1000,
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        t0 = time.time()

        resp = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            response_format={"type": "json_object"},
        )

        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            provider=self.name,
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            total_tokens=resp.usage.total_tokens if resp.usage else 0,
            finish_reason=resp.choices[0].finish_reason,
            latency_ms=(time.time() - t0) * 1000,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
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
