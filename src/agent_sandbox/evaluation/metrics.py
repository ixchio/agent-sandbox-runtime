"""
Metrics Collector
=================

Collects and aggregates metrics from benchmark runs.
"""

from datetime import datetime
from typing import Any

from agent_sandbox.contracts.agent_output import BenchmarkResult, BenchmarkSuiteResult


class MetricsCollector:
    """
    Collects metrics from benchmark runs.

    Tracks:
    - Pass/fail rates
    - Attempt counts
    - Execution times
    - Error categories
    """

    def __init__(self) -> None:
        self.results: list[BenchmarkResult] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def start(self) -> None:
        """Start metrics collection."""
        self.results = []
        self.start_time = datetime.utcnow()
        self.end_time = None

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def finish(self) -> None:
        """Finish metrics collection."""
        self.end_time = datetime.utcnow()

    def get_summary(self, suite_name: str = "benchmark") -> BenchmarkSuiteResult:
        """Get aggregated results."""
        if not self.results:
            return BenchmarkSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=0,
                success_rate=0.0,
                average_attempts=0.0,
                average_execution_time_ms=0.0,
                results=[],
            )

        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_attempts = sum(r.attempts for r in self.results)
        total_time = sum(r.execution_time_ms for r in self.results)

        return BenchmarkSuiteResult(
            suite_name=suite_name,
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            success_rate=passed / len(self.results),
            average_attempts=total_attempts / len(self.results),
            average_execution_time_ms=total_time / len(self.results),
            results=self.results,
        )

    def get_stats_by_category(self) -> dict[str, dict[str, Any]]:
        """Get stats grouped by problem category."""
        categories: dict[str, list[BenchmarkResult]] = {}

        for result in self.results:
            # Extract category from test_id prefix
            category = result.test_id.split("-")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        stats = {}
        for category, results in categories.items():
            passed = sum(1 for r in results if r.passed)
            stats[category] = {
                "total": len(results),
                "passed": passed,
                "failed": len(results) - passed,
                "success_rate": passed / len(results) if results else 0,
            }

        return stats

    def get_stats_by_difficulty(self) -> dict[str, dict[str, Any]]:
        """Get stats grouped by difficulty."""
        # This would require storing difficulty in results
        # For now, return empty
        return {}

    def generate_report(self) -> str:
        """Generate a markdown report of results."""
        summary = self.get_summary()
        category_stats = self.get_stats_by_category()

        report = f"""# Benchmark Report

## Summary
- **Total Tests:** {summary.total_tests}
- **Passed:** {summary.passed}
- **Failed:** {summary.failed}
- **Success Rate:** {summary.success_rate:.1%}
- **Average Attempts:** {summary.average_attempts:.2f}
- **Average Time:** {summary.average_execution_time_ms:.0f}ms
- **Improvement over Baseline:** {summary.improvement_over_baseline:+.1f}%

## By Category
| Category | Total | Passed | Failed | Rate |
|----------|-------|--------|--------|------|
"""

        for category, stats in category_stats.items():
            report += f"| {category} | {stats['total']} | {stats['passed']} | {stats['failed']} | {stats['success_rate']:.0%} |\n"

        report += """
## Failed Tests
"""

        failed = [r for r in self.results if not r.passed]
        if failed:
            for result in failed[:10]:  # Show top 10 failures
                report += f"- **{result.test_name}** ({result.test_id}): {result.error_message or 'Unknown error'}\n"
        else:
            report += "_All tests passed!_\n"

        return report
