"""
Retry Manager Node
==================

Manages the retry logic and decides when to continue or stop.
"""

from typing import Any

import structlog

logger = structlog.get_logger()


class RetryManagerNode:
    """
    Manages retry logic for the reflexion loop.

    Responsibilities:
    - Track attempt history
    - Decide if retry should continue
    - Apply exponential backoff (if needed)
    - Aggregate learning from failures
    """

    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Process retry decision.

        Args:
            state: Current agent state

        Returns:
            Updated state with retry decision
        """
        attempt = state.get("attempt", 1)
        should_retry = state.get("should_retry", False)
        max_attempts = state.get("max_attempts", self.max_attempts)

        # Add to history
        history = state.get("history", [])
        history_entry = {
            "attempt": attempt,
            "code": state.get("code", ""),
            "execution_result": state.get("execution_result"),
            "critique": state.get("critique"),
        }
        history.append(history_entry)

        # Check if we should continue
        can_continue = should_retry and attempt < max_attempts

        if can_continue:
            logger.info(
                "Will retry",
                attempt=attempt,
                max_attempts=max_attempts,
            )
        else:
            reason = "max attempts reached" if attempt >= max_attempts else "retry not recommended"
            logger.info(
                "Stopping retries",
                attempt=attempt,
                reason=reason,
            )

        return {
            "history": history,
            "should_retry": can_continue,
        }

    def should_continue(self, state: dict[str, Any]) -> str:
        """
        Determine next step in workflow.

        Returns:
            "generate" to retry generation
            "end" to finish workflow
        """
        if state.get("should_retry", False):
            return "generate"
        return "end"

    def get_accumulated_context(self, state: dict[str, Any]) -> str:
        """
        Build context from all previous attempts.

        This helps the generator learn from ALL past failures,
        not just the most recent one.
        """
        history = state.get("history", [])
        if not history:
            return ""

        context_parts = ["## Previous Attempts\n"]

        for entry in history:
            attempt_num = entry.get("attempt", 0)
            code = entry.get("code", "")[:500]  # Truncate
            result = entry.get("execution_result", {})
            critique = entry.get("critique", "")

            context_parts.append(f"""
### Attempt {attempt_num}
**Code snippet:**
```python
{code}...
```
**Result:** Exit code {result.get("exit_code", "N/A")}
**Critique:** {critique[:300] if critique else "N/A"}
""")

        return "\n".join(context_parts)
