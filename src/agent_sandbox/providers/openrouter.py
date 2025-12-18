"""
OpenRouter Provider
===================

OpenRouter API provider for access to 100+ models from various providers.
Great for testing different models or using premium models without individual API keys.
"""

import time
from collections.abc import AsyncIterator

import httpx
import structlog

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

logger = structlog.get_logger()


# Popular OpenRouter models for code
OPENROUTER_MODELS = {
    # Free models
    "meta-llama/llama-3.3-70b-instruct:free": "Llama 3.3 70B (Free)",
    "qwen/qwen-2.5-coder-32b-instruct:free": "Qwen 2.5 Coder 32B (Free)",
    "deepseek/deepseek-chat:free": "DeepSeek Chat (Free)",
    # Premium models
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "openai/gpt-4o": "GPT-4o",
    "google/gemini-pro-1.5": "Gemini Pro 1.5",
    "deepseek/deepseek-coder": "DeepSeek Coder",
    "mistralai/codestral-latest": "Codestral",
}


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter API provider.

    Features:
    - Access to 100+ models from one API
    - Pay-per-use pricing
    - Free tier available
    - Great for testing different models
    """

    name = "openrouter"
    supports_json_mode = True
    supports_streaming = True

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=config.base_url or self.BASE_URL,
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "HTTP-Referer": config.extra.get(
                    "site_url", "https://github.com/agent-sandbox-runtime"
                ),
                "X-Title": config.extra.get("site_name", "Agent Sandbox Runtime"),
            },
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion using OpenRouter."""
        start_time = time.time()

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        usage = data.get("usage", {})

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.config.model),
            provider=self.name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=data["choices"][0].get("finish_reason"),
            latency_ms=latency_ms,
            raw=data,
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate JSON completion using OpenRouter."""
        start_time = time.time()

        # Add JSON instruction to system prompt (not all models support response_format)
        json_system = system_prompt + "\n\nYou MUST respond with valid JSON only."

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        usage = data.get("usage", {})

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.config.model),
            provider=self.name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=data["choices"][0].get("finish_reason"),
            latency_ms=latency_ms,
            raw=data,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion using OpenRouter."""
        async with self.client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature or self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    chunk = json.loads(data)
                    if chunk["choices"][0]["delta"].get("content"):
                        yield chunk["choices"][0]["delta"]["content"]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
