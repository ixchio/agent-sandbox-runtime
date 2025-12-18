"""
Ollama Provider
===============

Ollama provider for running local LLM models.
Best for privacy-sensitive applications and offline use.
"""

import time
from collections.abc import AsyncIterator

import httpx
import structlog

from agent_sandbox.providers.base import LLMProvider, LLMResponse, ProviderConfig

logger = structlog.get_logger()


# Popular Ollama models for code
OLLAMA_MODELS = {
    "qwen2.5-coder:32b": "Qwen 2.5 Coder 32B - Best local coder",
    "qwen2.5-coder:14b": "Qwen 2.5 Coder 14B - Great balance",
    "qwen2.5-coder:7b": "Qwen 2.5 Coder 7B - Fast and capable",
    "codellama:34b": "Code Llama 34B - Meta's code model",
    "codellama:13b": "Code Llama 13B - Good for most tasks",
    "deepseek-coder-v2:16b": "DeepSeek Coder V2 16B",
    "llama3.2:3b": "Llama 3.2 3B - Fastest",
    "mistral:7b": "Mistral 7B - General purpose",
}


class OllamaProvider(LLMProvider):
    """
    Ollama local LLM provider.

    Features:
    - Run models locally
    - No API costs
    - Full privacy
    - Offline capable
    - JSON mode support (model dependent)

    Requires Ollama to be running: https://ollama.ai
    """

    name = "ollama"
    supports_json_mode = True  # Model dependent
    supports_streaming = True

    DEFAULT_URL = "http://localhost:11434"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=config.base_url or self.DEFAULT_URL,
            timeout=config.timeout * 2,  # Local models can be slower
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        start_time = time.time()

        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens,
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.config.model),
            provider=self.name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            finish_reason="stop" if data.get("done") else None,
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
        """Generate JSON completion using Ollama."""
        start_time = time.time()

        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",  # Enable JSON mode
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens,
                },
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.config.model),
            provider=self.name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            finish_reason="stop" if data.get("done") else None,
            latency_ms=latency_ms,
            raw=data,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion using Ollama."""
        async with self.client.stream(
            "POST",
            "/api/chat",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                import json

                try:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library."""
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model},
                timeout=600.0,  # Models can take a while to download
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
