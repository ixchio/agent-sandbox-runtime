import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main(suite: str, limit: int | None, output: str | None):
    """Run benchmrks."""
    from agent_sandbox.evaluation.runner import run_benchmarks

    print(f"Running benchmark suite: {suite}")
    if limit:
        print(f"Limiting to {limit} problems")
    print()

    results = await run_benchmarks(suite, limit)

    # Print summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    print(f"Suite: {results.suite_name}")
    print(f"Total: {results.total_tests}")
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Success Rate: {results.success_rate:.1%}")
    print(f"Avg Attempts: {results.average_attempts:.2f}")
    print(f"Avg Time: {results.average_execution_time_ms:.0f}ms")
    print(f"vs Baseline: {results.improvement_over_baseline:+.1f}%")
    print("=" * 50)

    # Save to file if requested
    if output:
        import json

        with open(output, "w") as f:
            json.dump(
                {
                    "suite": results.suite_name,
                    "total": results.total_tests,
                    "passed": results.passed,
                    "failed": results.failed,
                    "success_rate": results.success_rate,
                    "average_attempts": results.average_attempts,
                    "average_time_ms": results.average_execution_time_ms,
                    "results": [r.model_dump() for r in results.results],
                },
                f,
                indent=2,
            )
        print(f"\nResults saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run agent benchmarks")
    parser.add_argument(
        "--suite",
        "-s",
        default="quick",
        help="Benchmark suite to run (quick, full, algorithms, etc.)",
    )
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limit number of problems")
    parser.add_argument("--output", "-o", default=None, help="Output file for JSON results")

    args = parser.parse_args()
    asyncio.run(main(args.suite, args.limit, args.output))
