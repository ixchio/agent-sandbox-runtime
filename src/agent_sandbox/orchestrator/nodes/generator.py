"""Generator node - creates code from task descriptions."""

import json
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.contracts.agent_output import AgentOutput
from agent_sandbox.providers.base import LLMProvider
from agent_sandbox.providers.factory import create_provider

log = structlog.get_logger()

SYSTEM_PROMPT = """You are an expert Python programmer. Write clean, working code.

RULES:
1. Complete, runnable Python code
2. Include imports at the top
3. Print results to stdout
4. Handle edge cases
5. NO os.system, subprocess, or eval

OUTPUT FORMAT (JSON):
{
    "code": "your Python code",
    "dependencies": [],
    "reasoning": "your approach",
    "confidence": 0.85
}"""

RETRY_PROMPT = """Fix this broken code.

PREVIOUS CODE:
```python
{previous_code}
```

ERROR:
{error_context}

Return fixed code in JSON format with code, dependencies, reasoning, confidence fields."""


class GeneratorNode:
    """Generates Python code using LLM."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._provider: LLMProvider | None = None

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

    async def generate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate code for task. Called by LangGraph."""
        task = state.get("task", "")
        attempt = state.get("attempt", 0) + 1

        log.info("Generating", task=task[:50], attempt=attempt)

        if attempt == 1:
            system = SYSTEM_PROMPT
            user = f"Task: {task}"
        else:
            prev_code = state.get("code", "")
            error = state.get("critique", "") or self._extract_error(state)
            system = SYSTEM_PROMPT
            user = RETRY_PROMPT.format(previous_code=prev_code, error_context=error)

        try:
            resp = await self.provider.generate_json(
                system_prompt=system,
                user_prompt=user,
                temperature=0.2,
                max_tokens=4096,
            )

            output = self._parse(resp.content)

            log.info("Generated", attempt=attempt, lines=output.code.count("\n"))

            return {
                "code": output.code,
                "dependencies": output.dependencies,
                "reasoning": output.reasoning,
                "confidence": output.confidence,
                "attempt": attempt,
            }
        except Exception as e:
            log.error("Generation failed", error=str(e))
            return {"code": "", "reasoning": f"Failed: {e}", "attempt": attempt}

    def _parse(self, content: str) -> AgentOutput:
        try:
            return AgentOutput(**json.loads(content))
        except (json.JSONDecodeError, ValueError):
            code = content
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            return AgentOutput(code=code, dependencies=[], reasoning="Extracted", confidence=0.5)

    def _extract_error(self, state: dict) -> str:
        result = state.get("execution_result")
        if result:
            if hasattr(result, "get_error_summary"):
                return result.get_error_summary()
            if isinstance(result, dict):
                return result.get("stderr", "") or f"Exit: {result.get('exit_code', 1)}"
        return "Unknown error"
