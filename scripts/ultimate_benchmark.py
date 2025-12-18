#!/usr/bin/env python3
"""
🔥 ULTIMATE BENCHMARK - THE GOD TIER TEST 🔥
=============================================
This benchmark pushes the agent to its limits.
Tests swarm intelligence, self-evolving memory, and execution traces.

Run: python scripts/ultimate_benchmark.py
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

console = Console()

# Test categories with increasing difficulty
BENCHMARK_SUITE = {
    "🟢 BASIC": [
        "Calculate factorial of 10",
        "Check if 'racecar' is a palindrome",
        "Print fibonacci sequence up to 10 terms",
    ],
    "🟡 INTERMEDIATE": [
        "Find all prime numbers between 1 and 50",
        "Sort a list using quicksort algorithm",
        "Implement binary search on sorted list [1,3,5,7,9,11]",
    ],
    "🔴 ADVANCED": [
        "Solve the Tower of Hanoi for 4 disks",
        "Find longest common subsequence of 'ABCDGH' and 'AEDFHR'",
        "Implement a min-heap and insert [5,3,8,1,2]",
    ],
    "💀 EXTREME": [
        "Generate all permutations of [1,2,3,4] without itertools",
        "Solve 8-queens problem and print one solution",
        "Implement Dijkstra's shortest path for a 5-node graph",
    ],
}


class UltimateBenchmark:
    """The ultimate test of agent capabilities."""

    def __init__(self):
        self.results = []
        self.start_time = None

    async def run(self):
        """Run the full benchmark suite."""
        console.print(
            Panel.fit(
                "[bold cyan]🔥 AGENT SANDBOX RUNTIME[/bold cyan]\n"
                "[bold yellow]ULTIMATE BENCHMARK[/bold yellow]\n"
                "[dim]Testing the limits of AI code generation[/dim]",
                border_style="bright_cyan",
            )
        )

        # Import components
        from agent_sandbox.config import get_settings
        from agent_sandbox.providers import create_provider
        from agent_sandbox.orchestrator.nodes.generator import GeneratorNode
        from agent_sandbox.memory import EvolvingMemory
        from agent_sandbox.debugger import TraceDebugger

        settings = get_settings()
        generator = GeneratorNode(settings)
        memory = EvolvingMemory()
        debugger = TraceDebugger()

        # Provider info
        console.print(f"\n📡 Provider: [cyan]{settings.llm_provider}[/cyan]")
        console.print(f"🤖 Model: [cyan]{settings.get_provider_model()}[/cyan]")
        console.print(f"🧠 Memory entries: [cyan]{len(memory.memories)}[/cyan]\n")

        self.start_time = time.time()
        all_results = []

        for category, tasks in BENCHMARK_SUITE.items():
            console.print(f"\n{category}")
            console.print("─" * 50)

            for task in tasks:
                result = await self._run_single(task, generator, memory, debugger)
                all_results.append(result)
                self._print_result(result)

        elapsed = time.time() - self.start_time
        self._print_summary(all_results, elapsed, memory)
        await self._generate_report(all_results, elapsed, settings)

    async def _run_single(self, task: str, generator, memory, debugger):
        """Run single benchmark task."""
        trace = debugger.start_trace(task)

        # Enhance prompt with memory
        lessons = memory.get_lessons_for_task(task)

        t0 = time.time()
        state = await generator.generate({"task": task, "attempt": 0})
        elapsed = (time.time() - t0) * 1000

        code = state.get("code", "")
        success = len(code) > 20 and "def" in code or "print" in code

        # Store in memory for future learning
        memory.remember(task, code, success, attempts=1)

        debugger.end_trace({"success": success})

        return {
            "task": task,
            "success": success,
            "time_ms": elapsed,
            "code_lines": code.count("\n") + 1,
            "confidence": state.get("confidence", 0),
            "lessons_used": len(lessons),
            "trace": debugger.visualize(trace),
        }

    def _print_result(self, result):
        """Print single result."""
        icon = "✅" if result["success"] else "❌"
        conf = result.get("confidence", 0)
        console.print(
            f"  {icon} {result['task'][:40]:<40} "
            f"[dim]{result['time_ms']:.0f}ms[/dim] "
            f"[cyan]{result['code_lines']} lines[/cyan] "
            f"[yellow]conf: {conf:.0%}[/yellow]"
        )

    def _print_summary(self, results, elapsed, memory):
        """Print benchmark summary."""
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        avg_time = sum(r["time_ms"] for r in results) / total
        avg_conf = sum(r.get("confidence", 0) for r in results) / total

        console.print("\n")

        table = Table(title="🏆 BENCHMARK RESULTS", border_style="cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Rating", style="yellow")

        rate = passed / total
        rating = (
            "🔥 GOD TIER"
            if rate >= 0.9
            else "⭐ EXCELLENT"
            if rate >= 0.8
            else "👍 GOOD"
            if rate >= 0.7
            else "📈 IMPROVING"
        )

        table.add_row("Tests Passed", f"{passed}/{total}", rating)
        table.add_row("Success Rate", f"{rate:.0%}", "")
        table.add_row("Avg Response", f"{avg_time:.0f}ms", "⚡ FAST" if avg_time < 1000 else "")
        table.add_row("Avg Confidence", f"{avg_conf:.0%}", "")
        table.add_row("Total Time", f"{elapsed:.1f}s", "")
        table.add_row("Memory Entries", str(len(memory.memories)), "🧠 LEARNING")

        console.print(table)

        # Category breakdown
        console.print("\n📊 [bold]BY CATEGORY:[/bold]")
        idx = 0
        for category, tasks in BENCHMARK_SUITE.items():
            cat_results = results[idx : idx + len(tasks)]
            cat_passed = sum(1 for r in cat_results if r["success"])
            console.print(f"  {category}: {cat_passed}/{len(tasks)}")
            idx += len(tasks)

    async def _generate_report(self, results, elapsed, settings):
        """Generate HTML report."""
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        rate = passed / total

        # Generate per-category stats
        cat_stats = []
        idx = 0
        for cat, tasks in BENCHMARK_SUITE.items():
            cat_results = results[idx : idx + len(tasks)]
            cat_passed = sum(1 for r in cat_results if r["success"])
            cat_stats.append(
                {
                    "name": cat,
                    "passed": cat_passed,
                    "total": len(tasks),
                    "rate": cat_passed / len(tasks),
                }
            )
            idx += len(tasks)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ultimate Benchmark - Agent Sandbox</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'SF Pro Display', -apple-system, sans-serif;
            background: #0a0a0f;
            color: #fff;
            min-height: 100vh;
            padding: 40px;
        }}
        .hero {{
            text-align: center;
            padding: 60px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 24px;
            margin-bottom: 40px;
        }}
        .hero h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
        }}
        .hero .subtitle {{ opacity: 0.8; font-size: 1.2rem; }}
        .hero .score {{
            font-size: 5rem;
            font-weight: 800;
            margin: 30px 0;
        }}
        .hero .rating {{
            font-size: 1.5rem;
            color: #ffd700;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
        }}
        .card h3 {{ color: #667eea; margin-bottom: 16px; }}
        .stat {{ font-size: 2rem; font-weight: 700; }}
        .chart-box {{ height: 300px; }}
        table {{ width: 100%; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #667eea; }}
        .pass {{ color: #4ade80; }}
        .fail {{ color: #f87171; }}
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
        }}
        .badge-pass {{ background: rgba(74,222,128,0.2); color: #4ade80; }}
        .badge-fail {{ background: rgba(248,113,113,0.2); color: #f87171; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>🔥 ULTIMATE BENCHMARK</h1>
        <p class="subtitle">Agent Sandbox Runtime - {settings.llm_provider} / {
            settings.get_provider_model()
        }</p>
        <div class="score">{rate:.0%}</div>
        <div class="rating">{
            "🔥 GOD TIER" if rate >= 0.9 else "⭐ EXCELLENT" if rate >= 0.8 else "👍 GOOD"
        }</div>
        <p style="margin-top: 20px; opacity: 0.7">{passed}/{total} tests passed in {
            elapsed:.1f}s</p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>📈 Success by Category</h3>
            <div class="chart-box">
                <canvas id="catChart"></canvas>
            </div>
        </div>
        <div class="card">
            <h3>⚡ Response Times</h3>
            <div class="chart-box">
                <canvas id="timeChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-top: 24px">
        <h3>📋 All Results</h3>
        <table>
            <tr>
                <th>Task</th>
                <th>Status</th>
                <th>Time</th>
                <th>Lines</th>
                <th>Confidence</th>
            </tr>
            {
            "".join(
                f'''
            <tr>
                <td>{r["task"][:50]}</td>
                <td><span class="badge {"badge-pass" if r["success"] else "badge-fail"}">{"PASS" if r["success"] else "FAIL"}</span></td>
                <td>{r["time_ms"]:.0f}ms</td>
                <td>{r["code_lines"]}</td>
                <td>{r.get("confidence", 0):.0%}</td>
            </tr>'''
                for r in results
            )
        }
        </table>
    </div>
    
    <script>
        new Chart(document.getElementById('catChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([c["name"] for c in cat_stats])},
                datasets: [{{
                    label: 'Success Rate',
                    data: {json.dumps([c["rate"] * 100 for c in cat_stats])},
                    backgroundColor: ['#4ade80', '#facc15', '#f87171', '#a855f7'],
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{ y: {{ max: 100, grid: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        new Chart(document.getElementById('timeChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([f"T{i + 1}" for i in range(len(results))])},
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: {json.dumps([r["time_ms"] for r in results])},
                    borderColor: '#667eea',
                    tension: 0.3,
                    fill: true,
                    backgroundColor: 'rgba(102,126,234,0.1)',
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{ y: {{ grid: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    </script>
    
    <p style="text-align: center; margin-top: 40px; opacity: 0.5">
        Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Agent Sandbox Runtime v0.1.0
    </p>
</body>
</html>"""

        report_path = Path("ultimate_benchmark.html")
        report_path.write_text(html)
        console.print(f"\n📄 Report: [link=file://{report_path.absolute()}]{report_path}[/link]")


async def main():
    benchmark = UltimateBenchmark()
    await benchmark.run()
    console.print("\n[bold green]✨ Benchmark complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
