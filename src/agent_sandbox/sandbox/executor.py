"""Code Executor - High-level interface for sandboxed code execution."""

from collections.abc import Callable

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.sandbox.manager import SandboxManager
from agent_sandbox.sandbox.models import ExecutionRequest, ExecutionResult

logger = structlog.get_logger()


class CodeExecutor:
    """
    High-level code execution interface.

    Provides a simple API for executing code with automatic
    dependency installation and error handling.
    """

    def __init__(
        self,
        sandbox_manager: SandboxManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._sandbox_manager = sandbox_manager
        self._owns_manager = sandbox_manager is None

    async def __aenter__(self) -> "CodeExecutor":
        """Async context manager entry."""
        if self._sandbox_manager is None:
            self._sandbox_manager = SandboxManager(self.settings)
            await self._sandbox_manager.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._owns_manager and self._sandbox_manager:
            await self._sandbox_manager.cleanup()

    @property
    def sandbox(self) -> SandboxManager:
        """Get the sandbox manager."""
        if self._sandbox_manager is None:
            raise RuntimeError("Executor not initialized. Use async context manager.")
        return self._sandbox_manager

    async def execute(
        self,
        code: str,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        network: bool = False,
    ) -> ExecutionResult:
        """
        Execute Python code in a sandboxed environment.

        Args:
            code: Python code to execute
            dependencies: Optional list of pip packages to install
            timeout: Optional timeout override in seconds
            network: Enable network access (default False)

        Returns:
            ExecutionResult with stdout, stderr, and metadata
        """
        request = ExecutionRequest(
            code=code,
            language="python",
            dependencies=dependencies or [],
            timeout_seconds=timeout or self.settings.sandbox_timeout_seconds,
            memory_limit_mb=self.settings.sandbox_memory_limit_mb,
            network_enabled=network,
        )

        return await self.sandbox.execute(request)

    async def execute_with_retry(
        self,
        code: str,
        dependencies: list[str] | None = None,
        max_retries: int = 3,
        fix_callback: Callable | None = None,
    ) -> tuple[ExecutionResult, int]:
        """
        Execute code with automatic retry on failure.

        This is used by the reflexion loop to implement
        self-correcting behavior.

        Args:
            code: Python code to execute
            dependencies: Optional pip packages
            max_retries: Maximum retry attempts
            fix_callback: Async function that takes (code, error) and returns fixed code

        Returns:
            Tuple of (final result, number of attempts)
        """
        current_code = code
        attempts = 0

        for attempt in range(max_retries):
            attempts = attempt + 1

            result = await self.execute(
                code=current_code,
                dependencies=dependencies,
            )

            if result.is_success:
                logger.info(
                    "Execution succeeded",
                    attempt=attempts,
                )
                return result, attempts

            if fix_callback and attempt < max_retries - 1:
                error = result.get_error_summary()
                logger.info(
                    "Execution failed, requesting fix",
                    attempt=attempts,
                    error=error[:200],
                )

                # Get fixed code from callback
                current_code = await fix_callback(current_code, error)
            else:
                logger.warning(
                    "Execution failed, no more retries",
                    attempt=attempts,
                    error=result.get_error_summary()[:200],
                )

        return result, attempts
