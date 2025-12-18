"""
Agent Runtime
==============

High-level API for running the self-correcting agent.
"""

from collections.abc import AsyncGenerator
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.contracts.agent_output import BenchmarkSuiteResult
from agent_sandbox.orchestrator.graph import AgentGraph
from agent_sandbox.sandbox.manager import SandboxManager

logger = structlog.get_logger()


class AgentRuntime:
    """
    High-level runtime for the self-correcting agent.

    This is the main entry point for using the agent.
    Handles sandbox initialization, cleanup, and provides
    a clean async API.

    Usage:
        async with AgentRuntime() as runtime:
            result = await runtime.run("Write a fibonacci function")
            print(result.output)
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._sandbox_manager: SandboxManager | None = None
        self._agent: AgentGraph | None = None
        self._initialized = False

    async def __aenter__(self) -> "AgentRuntime":
        """Initialize runtime."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup runtime."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize the sandbox and agent."""
        if self._initialized:
            return

        logger.info("Initializing agent runtime")

        self._sandbox_manager = SandboxManager(self.settings)
        await self._sandbox_manager.initialize()

        self._agent = AgentGraph(self._sandbox_manager, self.settings)

        self._initialized = True
        logger.info("Agent runtime initialized")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._sandbox_manager:
            await self._sandbox_manager.cleanup()

        self._sandbox_manager = None
        self._agent = None
        self._initialized = False

        logger.info("Agent runtime cleaned up")

    @property
    def sandbox(self) -> SandboxManager:
        """Get sandbox manager."""
        if not self._sandbox_manager:
            raise RuntimeError("Runtime not initialized")
        return self._sandbox_manager

    @property
    def agent(self) -> AgentGraph:
        """Get agent graph."""
        if not self._agent:
            raise RuntimeError("Runtime not initialized")
        return self._agent

    async def run(
        self,
        task: str,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        """
        Run the agent on a task.

        Args:
            task: Task description
            max_attempts: Optional max retry attempts

        Returns:
            Result dictionary with:
            - success: bool
            - code: str
            - output: str
            - attempts: int
            - reasoning: str
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized. Use async context manager.")

        result = await self.agent.run(task, max_attempts)

        return {
            "success": result.get("success", False),
            "code": result.get("code", ""),
            "output": result.get("final_output", ""),
            "attempts": result.get("attempt", 1),
            "reasoning": result.get("reasoning", ""),
            "dependencies": result.get("dependencies", []),
            "history": result.get("history", []),
        }

    async def run_streaming(
        self,
        task: str,
        max_attempts: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Run the agent with streaming updates.

        Yields state updates as the workflow progresses.
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")

        async for event in self.agent.run_streaming(task, max_attempts):
            yield event

    async def run_benchmark(
        self,
        suite: str = "quick",
        max_problems: int | None = None,
    ) -> BenchmarkSuiteResult:
        """
        Run benchmark suite.

        Args:
            suite: Benchmark suite name
            max_problems: Optional problem limit

        Returns:
            Benchmark results
        """
        from agent_sandbox.evaluation.runner import BenchmarkRunner

        if not self._initialized:
            raise RuntimeError("Runtime not initialized")

        runner = BenchmarkRunner(self.sandbox, self.settings)
        return await runner.run_suite(suite, max_problems)


async def quick_run(task: str, max_attempts: int = 3) -> dict[str, Any]:
    """
    Convenience function for quick one-off runs.

    Usage:
        result = await quick_run("Calculate fibonacci(10)")
        print(result["output"])
    """
    async with AgentRuntime() as runtime:
        return await runtime.run(task, max_attempts)
