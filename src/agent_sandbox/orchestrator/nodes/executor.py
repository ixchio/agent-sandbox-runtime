"""
Executor Node
=============

Executes generated code in the Docker sandbox.
"""

from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.sandbox.manager import SandboxManager
from agent_sandbox.sandbox.models import ExecutionRequest, ExecutionResult, ExecutionStatus

logger = structlog.get_logger()


class ExecutorNode:
    """
    Executes code in the sandboxed environment.

    This node takes generated code and runs it in a Docker container
    with strict resource limits and security constraints.
    """

    def __init__(
        self,
        sandbox_manager: SandboxManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._sandbox_manager = sandbox_manager

    def set_sandbox_manager(self, manager: SandboxManager) -> None:
        """Set the sandbox manager (used for dependency injection)."""
        self._sandbox_manager = manager

    @property
    def sandbox(self) -> SandboxManager:
        """Get sandbox manager."""
        if self._sandbox_manager is None:
            raise RuntimeError("Sandbox manager not set. Call set_sandbox_manager() first.")
        return self._sandbox_manager

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the generated code in sandbox.

        Args:
            state: Current agent state with code

        Returns:
            Updated state with execution result
        """
        code = state.get("code", "")
        dependencies = state.get("dependencies", [])
        attempt = state.get("attempt", 1)

        if not code:
            logger.warning("No code to execute")
            return {
                "execution_result": ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stderr="No code provided",
                    exit_code=1,
                ).model_dump(),
            }

        logger.info(
            "Executing code in sandbox",
            attempt=attempt,
            code_length=len(code),
            dependencies=dependencies,
        )

        try:
            # Create execution request
            request = ExecutionRequest(
                code=code,
                dependencies=dependencies,
                timeout_seconds=self.settings.sandbox_timeout_seconds,
                memory_limit_mb=self.settings.sandbox_memory_limit_mb,
                network_enabled=self.settings.sandbox_network_enabled,
            )

            # Execute in sandbox
            result = await self.sandbox.execute(request)

            logger.info(
                "Execution completed",
                attempt=attempt,
                status=result.status.value,
                exit_code=result.exit_code,
                execution_time_ms=result.execution_time_ms,
            )

            return {
                "execution_result": result.model_dump(),
            }

        except Exception as e:
            logger.error("Execution failed", error=str(e))
            return {
                "execution_result": ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stderr=f"Execution error: {str(e)}",
                    exit_code=1,
                ).model_dump(),
            }

    def should_continue(self, state: dict[str, Any]) -> str:
        """
        Determine the next node based on execution result.

        Returns:
            "success" if code ran successfully
            "critique" if code failed and needs review
            "end" if max attempts reached
        """
        result_dict = state.get("execution_result", {})
        attempt = state.get("attempt", 1)
        max_attempts = state.get("max_attempts", 3)

        # Check for success
        exit_code = result_dict.get("exit_code", 1)
        stderr = result_dict.get("stderr", "")
        timed_out = result_dict.get("timed_out", False)

        if exit_code == 0 and not stderr and not timed_out:
            logger.info("Execution successful, ending workflow")
            return "success"

        # Check if we can retry
        if attempt >= max_attempts:
            logger.warning(
                "Max attempts reached",
                attempt=attempt,
                max_attempts=max_attempts,
            )
            return "end"

        logger.info(
            "Execution failed, routing to critic",
            attempt=attempt,
            exit_code=exit_code,
        )
        return "critique"
