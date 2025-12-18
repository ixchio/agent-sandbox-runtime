import time
from collections.abc import AsyncIterator

import httpx
import structlog

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

logger = structlog.get_logger()


# Anthropic Claude models
ANTHROPIC_MODELS = {
    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Latest) - Best for code",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (Latest) - Fast and capable",
    "claude-3-opus-20240229": "Claude 3 Opus - Most powerful",
    "claude-3-sonnet-20240229": "Claude 3 Sonnet - Balanced",
    "claude-3-haiku-20240307": "Claude 3 Haiku - Fastest",
}


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    supports_json_mode = True  # Via prompting
    supports_streaming = True

    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=config.base_url or self.BASE_URL,
            timeout=config.timeout,
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion using Claude."""
        start_time = time.time()

        response = await self.client.post(
            "/messages",
            json={
                "model": self.config.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        # Extract content from Anthropic's response format
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model),
            provider=self.name,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            finish_reason=data.get("stop_reason"),
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
        """Generate JSON completion using Claude."""
        # Claude doesn't have native JSON mode, use prompting
        json_system = (
            system_prompt
            + """

CRITICAL: You MUST respond with valid JSON only. No markdown code blocks, no explanation.
Start your response with '{' and end with '}'. Nothing else."""
        )

        return await self.generate(
            system_prompt=json_system,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion using Claude."""
        async with self.client.stream(
            "POST",
            "/messages",
            json={
                "model": self.config.model,
                "system": system_prompt,
                "messages": [
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
                    import json

                    try:
                        event = json.loads(data)
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
