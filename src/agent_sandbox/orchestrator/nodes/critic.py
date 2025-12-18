"""Critic node - analyzes failures and suggests fixes."""

import json
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.providers.base import LLMProvider
from agent_sandbox.providers.factory import create_provider

log = structlog.get_logger()

SYSTEM_PROMPT = """You analyze why Python code failed and suggest fixes.

Check for:
- Syntax errors
- Import issues
- Logic bugs
- Type mismatches
- Edge cases

OUTPUT (JSON):
{
    "diagnosis": "what went wrong",
    "fix_suggestion": "how to fix it",
    "should_retry": true,
    "confidence": 0.85
}"""


class CriticNode:
    """Reviews failed executions and provides feedback."""

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

    async def critique(self, state: dict[str, Any]) -> dict[str, Any]:
        """Review failed code. Called by LangGraph."""
        task = state.get("task", "")
        code = state.get("code", "")
        result = state.get("execution_result", {})
        attempt = state.get("attempt", 1)

        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", 1)
        timed_out = result.get("timed_out", False)

        error = stderr
        if timed_out:
            error = f"Timed out. {stderr}"

        log.info("Critiquing", attempt=attempt, exit_code=exit_code)

        prompt = f"""TASK: {task}

CODE:
```python
{code}
```

ERROR (exit {exit_code}):
{error[:2000]}

Attempt {attempt} of {state.get("max_attempts", 3)}. Analyze and suggest fix."""

        try:
            resp = await self.provider.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=1024,
            )

            data = self._parse(resp.content)

            critique = f"## Diagnosis\n{data.get('diagnosis', 'Unknown')}\n\n## Fix\n{data.get('fix_suggestion', 'Review error')}"
            should_retry = data.get("should_retry", True)

            log.info("Critique done", should_retry=should_retry)

            return {"critique": critique, "should_retry": should_retry}
        except Exception as e:
            log.error("Critique failed", error=str(e))
            return {"critique": f"Review failed: {e}", "should_retry": True}

    def _parse(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"diagnosis": content, "fix_suggestion": "Check syntax", "should_retry": True}
