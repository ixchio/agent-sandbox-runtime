"""
Google Provider
===============

Google Gemini API provider.
Great for multimodal tasks and large context windows.
"""

import time
from collections.abc import AsyncIterator

import httpx
import structlog

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

logger = structlog.get_logger()


# Gemini models
GOOGLE_MODELS = {
    "gemini-2.0-flash-exp": "Gemini 2.0 Flash (Experimental) - Latest",
    "gemini-1.5-pro": "Gemini 1.5 Pro - Best for complex tasks",
    "gemini-1.5-flash": "Gemini 1.5 Flash - Fast and efficient",
    "gemini-1.5-flash-8b": "Gemini 1.5 Flash 8B - Fastest",
}


class GoogleProvider(LLMProvider):
    """
    Google Gemini API provider.

    Features:
    - Large context windows (up to 2M tokens)
    - Multimodal capabilities
    - Native JSON mode
    - Fast inference
    """

    name = "google"
    supports_json_mode = True
    supports_streaming = True

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
        )
        self.api_key = config.api_key
        self.base_url = config.base_url or self.BASE_URL

    def _get_url(self, model: str, method: str = "generateContent") -> str:
        """Build API URL."""
        return f"{self.base_url}/models/{model}:{method}?key={self.api_key}"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion using Gemini."""
        start_time = time.time()

        response = await self.client.post(
            self._get_url(self.config.model),
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": temperature or self.config.temperature,
                    "maxOutputTokens": max_tokens or self.config.max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        # Extract content
        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                content += part.get("text", "")

        # Usage metadata
        usage = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.name,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidates[0].get("finishReason") if candidates else None,
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
        """Generate JSON completion using Gemini."""
        start_time = time.time()

        response = await self.client.post(
            self._get_url(self.config.model),
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": temperature or self.config.temperature,
                    "maxOutputTokens": max_tokens or self.config.max_tokens,
                    "responseMimeType": "application/json",
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                content += part.get("text", "")

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.name,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidates[0].get("finishReason") if candidates else None,
            latency_ms=latency_ms,
            raw=data,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion using Gemini."""
        async with self.client.stream(
            "POST",
            self._get_url(self.config.model, "streamGenerateContent"),
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": temperature or self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                import json

                try:
                    data = json.loads(line)
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if part.get("text"):
                                yield part["text"]
                except json.JSONDecodeError:
                    continue

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
