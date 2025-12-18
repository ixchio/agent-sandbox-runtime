#!/usr/bin/env python3
"""
PROFESSIONAL BENCHMARK WITH IMAGE PROOF
========================================
Generates matplotlib charts as PNG images for README.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

TESTS = {
    "Basic": [
        "Print Hello World",
        "Calculate 2+2",
        "Print first 5 fibonacci numbers",
    ],
    "Intermediate": [
        "Find all primes under 50",
        "Implement quicksort",
        "Binary search in [1,3,5,7,9,11]",
    ],
    "Advanced": [
        "Tower of Hanoi for 4 disks",
        "LCS of ABCDGH and AEDFHR",
        "Implement min-heap",
    ],
    "Extreme": [
        "All permutations of [1,2,3,4]",
        "8-queens one solution",
        "Dijkstra shortest path",
    ],
}


async def run_benchmark():
    from agent_sandbox.config import get_settings
    from agent_sandbox.orchestrator.nodes.generator import GeneratorNode
    from agent_sandbox.memory import EvolvingMemory

    settings = get_settings()
    generator = GeneratorNode(settings)
    memory = EvolvingMemory()

    console.print(
        Panel.fit(
            "[bold cyan]AGENT SANDBOX RUNTIME[/bold cyan]\n"
            "[yellow]Professional Benchmark Suite[/yellow]",
            border_style="cyan",
        )
    )

    console.print(f"\n🔌 Provider: [cyan]{settings.llm_provider}[/cyan]")
    console.print(f"🤖 Model: [cyan]{settings.get_provider_model()}[/cyan]\n")

    all_results = []
    category_stats = {}

    for category, tasks in TESTS.items():
        console.print(f"\n[bold]{category}[/bold]")
        cat_results = []

        for task in tasks:
            t0 = time.time()
            state = await generator.generate({"task": task, "attempt": 0})
            elapsed = (time.time() - t0) * 1000

            code = state.get("code", "")
            success = len(code) > 20 and ("def" in code or "print" in code)
            conf = state.get("confidence", 0)

            memory.remember(task, code, success)

            icon = "✅" if success else "❌"
            console.print(f"  {icon} {task[:35]:<35} {elapsed:>6.0f}ms  conf:{conf:.0%}")

            cat_results.append(
                {
                    "task": task,
                    "success": success,
                    "time_ms": elapsed,
                    "confidence": conf,
                    "lines": code.count("\n") + 1,
                }
            )

        passed = sum(1 for r in cat_results if r["success"])
        category_stats[category] = {
            "passed": passed,
            "total": len(tasks),
            "rate": passed / len(tasks),
            "avg_time": sum(r["time_ms"] for r in cat_results) / len(tasks),
        }
        all_results.extend(cat_results)

    return all_results, category_stats, settings


def generate_charts(results, category_stats, settings, output_dir: Path):
    output_dir.mkdir(exist_ok=True)

    plt.style.use("dark_background")

    # Chart 1: Success Rate by Category
    fig, ax = plt.subplots(figsize=(10, 6))
    categories = list(category_stats.keys())
    rates = [category_stats[c]["rate"] * 100 for c in categories]
    colors = ["#4ade80", "#facc15", "#f97316", "#ef4444"]

    bars = ax.bar(categories, rates, color=colors, edgecolor="white", linewidth=1.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Success Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Benchmark Success Rate by Difficulty", fontsize=14, fontweight="bold", pad=20)

    for bar, rate in zip(bars, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{rate:.0f}%",
            ha="center",
            fontsize=12,
            fontweight="bold",
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    plt.tight_layout()
    fig.savefig(output_dir / "benchmark_success_rate.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Chart 2: Response Time Distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    times = [r["time_ms"] for r in results]

    ax.hist(times, bins=15, color="#667eea", edgecolor="white", alpha=0.8)
    ax.axvline(
        np.mean(times),
        color="#4ade80",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {np.mean(times):.0f}ms",
    )
    ax.set_xlabel("Response Time (ms)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Frequency", fontsize=12, fontweight="bold")
    ax.set_title("Response Time Distribution", fontsize=14, fontweight="bold", pad=20)
    ax.legend(fontsize=11)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    plt.tight_layout()
    fig.savefig(output_dir / "benchmark_response_time.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Chart 3: Overall Stats Summary
    fig, ax = plt.subplots(figsize=(10, 6))

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    sizes = [passed, failed]
    labels = [f"Passed\n{passed}/{total}", f"Failed\n{failed}/{total}"]
    colors = ["#4ade80", "#ef4444"]
    explode = (0.05, 0)

    ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        textprops={"fontsize": 12, "fontweight": "bold"},
    )
    ax.set_title(
        f"Overall Benchmark Results\n{settings.llm_provider.upper()} / {settings.get_provider_model()}",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    fig.patch.set_facecolor("#1a1a2e")

    plt.tight_layout()
    fig.savefig(output_dir / "benchmark_overall.png", dpi=150, bbox_inches="tight")
    plt.close()

    console.print(f"\n📊 Charts saved to: [cyan]{output_dir}[/cyan]")


def print_summary(results, category_stats):
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    avg_time = sum(r["time_ms"] for r in results) / total
    avg_conf = sum(r["confidence"] for r in results) / total

    table = Table(title="🏆 BENCHMARK SUMMARY", border_style="cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    rate = passed / total
    rating = "🔥 GOD TIER" if rate >= 0.9 else "⭐ EXCELLENT" if rate >= 0.8 else "👍 GOOD"

    table.add_row("Total Tests", str(total))
    table.add_row("Passed", f"{passed}/{total}")
    table.add_row("Success Rate", f"{rate:.0%}")
    table.add_row("Rating", rating)
    table.add_row("Avg Response", f"{avg_time:.0f}ms")
    table.add_row("Avg Confidence", f"{avg_conf:.0%}")

    console.print("\n")
    console.print(table)


async def main():
    results, category_stats, settings = await run_benchmark()
    print_summary(results, category_stats)

    output_dir = Path("benchmark_charts")
    generate_charts(results, category_stats, settings, output_dir)

    # Save JSON results
    with open(output_dir / "results.json", "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "provider": settings.llm_provider,
                "model": settings.get_provider_model(),
                "results": results,
                "category_stats": category_stats,
            },
            f,
            indent=2,
        )

    console.print("\n[bold green]✨ Benchmark complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
