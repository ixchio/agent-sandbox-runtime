"""Validation retry loop - forces valid structured output."""

import json
from typing import TypeVar

import structlog
from pydantic import BaseModel, ValidationError

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.providers.base import LLMProvider
from agent_sandbox.providers.factory import create_provider

log = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)

RETRY_PROMPT = """Invalid response. Fix it.

ERROR: {error}

ORIGINAL: {response}

Return valid JSON matching the schema."""


class ValidationRetryLoop:
    """Retries LLM until output validates against schema."""

    def __init__(self, settings: Settings | None = None, max_retries: int = 3) -> None:
        self.settings = settings or get_settings()
        self._provider: LLMProvider | None = None
        self.max_retries = max_retries

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = create_provider(
                provider_type=self.settings.llm_provider,
                api_key=self.settings.get_provider_api_key(),
                model=self.settings.get_provider_model(),
                base_url=self.settings.get_provider_base_url(),
            )
        return self._provider

    async def validate_and_retry(
        self,
        response: str,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> T:
        """Validate response, retry with feedback if invalid."""
        current = response
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                data = json.loads(current)
                result = schema.model_validate(data)
                if attempt > 0:
                    log.info("Validation ok after retry", attempt=attempt + 1)
                return result
            except json.JSONDecodeError as e:
                last_error = e
                error_msg = f"Bad JSON: {e}"
                log.warning("JSON error", attempt=attempt + 1)
            except ValidationError as e:
                last_error = e
                error_msg = str(e)
                log.warning("Validation error", attempt=attempt + 1, errors=e.error_count())

            if attempt < self.max_retries - 1:
                current = await self._retry(error_msg, current, system_prompt, user_prompt)

        log.error("Validation failed", max_retries=self.max_retries)
        raise last_error or ValidationError("Unknown error")

    async def _retry(self, error: str, original: str, system: str, user: str) -> str:
        prompt = RETRY_PROMPT.format(error=error, response=original[:1000])
        resp = await self.provider.generate_json(system, f"{user}\n\n{prompt}", 0.1, 4096)
        return resp.content
