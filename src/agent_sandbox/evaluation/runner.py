"""
Benchmark Runner
================

Runs the agent against benchmark problems and collects metrics.

This is the "Staff Engineer" feature that quantifies agent performance
and proves the value of the reflexion loop.
"""

from datetime import datetime
from typing import Any

import structlog

from agent_sandbox.config import Settings, get_settings
from agent_sandbox.contracts.agent_output import BenchmarkResult, BenchmarkSuiteResult
from agent_sandbox.evaluation.metrics import MetricsCollector
from agent_sandbox.evaluation.problems import (
    BenchmarkProblem,
    get_suite,
)
from agent_sandbox.orchestrator.graph import AgentGraph
from agent_sandbox.sandbox.manager import SandboxManager

logger = structlog.get_logger()


class BenchmarkRunner:
    """
    Runs benchmarks against the agent.

    This lets you measure:
    - Success rate
    - Average attempts (reflexion effectiveness)
    - Execution time
    - Category-specific performance

    Usage:
        runner = BenchmarkRunner(sandbox_manager)
        results = await runner.run_suite("quick")
        print(f"Pass rate: {results.success_rate:.1%}")
    """

    def __init__(
        self,
        sandbox_manager: SandboxManager,
        settings: Settings | None = None,
    ) -> None:
        self.sandbox_manager = sandbox_manager
        self.settings = settings or get_settings()
        self.metrics = MetricsCollector()

    async def run_suite(
        self,
        suite_name: str = "quick",
        max_problems: int | None = None,
    ) -> BenchmarkSuiteResult:
        """
        Run a benchmark suite.

        Args:
            suite_name: Name of suite (quick, full, algorithms, etc.)
            max_problems: Optional limit on number of problems

        Returns:
            Aggregated benchmark results
        """
        problems = get_suite(suite_name)

        if max_problems:
            problems = problems[:max_problems]

        logger.info(
            "Starting benchmark suite",
            suite=suite_name,
            problem_count=len(problems),
        )

        self.metrics.start()

        for i, problem in enumerate(problems):
            logger.info(
                "Running problem",
                index=i + 1,
                total=len(problems),
                problem_id=problem.id,
                problem_name=problem.name,
            )

            result = await self.run_problem(problem)
            self.metrics.add_result(result)

            logger.info(
                "Problem completed",
                problem_id=problem.id,
                passed=result.passed,
                attempts=result.attempts,
                time_ms=result.execution_time_ms,
            )

        self.metrics.finish()

        summary = self.metrics.get_summary(suite_name)

        logger.info(
            "Benchmark suite completed",
            suite=suite_name,
            total=summary.total_tests,
            passed=summary.passed,
            success_rate=f"{summary.success_rate:.1%}",
            improvement=f"{summary.improvement_over_baseline:+.1f}%",
        )

        return summary

    async def run_problem(self, problem: BenchmarkProblem) -> BenchmarkResult:
        """
        Run a single benchmark problem.

        Args:
            problem: The benchmark problem to run

        Returns:
            Result of the benchmark run
        """
        start_time = datetime.utcnow()

        try:
            # Create agent
            agent = AgentGraph(self.sandbox_manager, self.settings)

            # Run agent on task
            result = await agent.run(
                task=problem.task,
                max_attempts=self.settings.max_reflexion_attempts,
            )

            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            # Check if result matches expected output
            passed = self._check_result(problem, result)

            return BenchmarkResult(
                test_id=problem.id,
                test_name=problem.name,
                passed=passed,
                attempts=result.get("attempt", 1),
                execution_time_ms=execution_time_ms,
                error_message=None if passed else result.get("final_output", ""),
                code_generated=result.get("code"),
                stdout=result.get("final_output") if passed else None,
            )

        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            logger.error(
                "Problem execution failed",
                problem_id=problem.id,
                error=str(e),
            )

            return BenchmarkResult(
                test_id=problem.id,
                test_name=problem.name,
                passed=False,
                attempts=1,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )

    def _check_result(
        self,
        problem: BenchmarkProblem,
        result: dict[str, Any],
    ) -> bool:
        """
        Check if result matches expected output.

        Supports:
        - expected_output: Exact match
        - expected_contains: List of substrings that must be present
        """
        if not result.get("success"):
            return False

        output = result.get("final_output", "")

        # Check exact match
        if problem.expected_output and problem.expected_output.strip() != output.strip():
            return False

        # Check contains
        if problem.expected_contains:
            output_lower = output.lower()
            for expected in problem.expected_contains:
                if expected.lower() not in output_lower:
                    return False

        return True

    def generate_report(self) -> str:
        """Generate a markdown report of results."""
        return self.metrics.generate_report()


async def run_benchmarks(
    suite_name: str = "quick",
    max_problems: int | None = None,
) -> BenchmarkSuiteResult:
    """
    Convenience function to run benchmarks.

    Creates sandbox manager, runs benchmarks, and cleans up.
    """
    settings = get_settings()
    sandbox_manager = SandboxManager(settings)

    try:
        await sandbox_manager.initialize()

        runner = BenchmarkRunner(sandbox_manager, settings)
        results = await runner.run_suite(suite_name, max_problems)

        # Print report
        print(runner.generate_report())

        return results

    finally:
        await sandbox_manager.cleanup()
