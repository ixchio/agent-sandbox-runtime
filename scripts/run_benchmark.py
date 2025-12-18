#!/usr/bin/env python3
"""
Real Benchmark Runner with Graphs
=================================
Run: python scripts/run_benchmark.py
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# Rich console output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel

    RICH = True
except ImportError:
    RICH = False


console = Console() if RICH else None


def print_msg(msg, style=None):
    if console:
        console.print(msg, style=style)
    else:
        print(msg)


async def test_provider():
    """Test LLM provider connection."""
    from agent_sandbox.config import get_settings
    from agent_sandbox.providers import create_provider

    settings = get_settings()
    provider = create_provider(
        settings.llm_provider,
        settings.get_provider_api_key(),
        settings.get_provider_model(),
    )

    print_msg(f"\n🔌 Testing {settings.llm_provider} ({settings.get_provider_model()})...")

    t0 = time.time()
    resp = await provider.generate(
        "You are a helpful assistant.",
        "Say 'OK' if you're working.",
        max_tokens=20,
    )
    latency = (time.time() - t0) * 1000

    print_msg(f"   Response: {resp.content.strip()}", style="green")
    print_msg(f"   Latency: {latency:.0f}ms", style="dim")

    return {
        "provider": settings.llm_provider,
        "model": settings.get_provider_model(),
        "latency_ms": latency,
    }


async def run_code_generation_tests():
    """Test code generation quality."""
    from agent_sandbox.config import get_settings
    from agent_sandbox.orchestrator.nodes.generator import GeneratorNode

    print_msg("\n🧪 Running Code Generation Tests...")

    generator = GeneratorNode(get_settings())

    tests = [
        {"task": "Print 'Hello World'", "check": "hello"},
        {"task": "Calculate 2+2 and print the result", "check": "4"},
        {"task": "Print the first 5 fibonacci numbers", "check": "1"},
        {"task": "Create a function to check if a number is prime, test with 7", "check": "true"},
        {"task": "Print all even numbers from 1 to 10", "check": "2"},
    ]

    results = []
    for i, test in enumerate(tests):
        print_msg(f"\n   [{i + 1}/{len(tests)}] {test['task'][:50]}...")

        t0 = time.time()
        state = await generator.generate({"task": test["task"], "attempt": 0})
        elapsed = (time.time() - t0) * 1000

        code = state.get("code", "")
        has_code = len(code) > 10
        looks_valid = test["check"].lower() in code.lower() or "print" in code.lower()

        results.append(
            {
                "task": test["task"],
                "success": has_code and looks_valid,
                "time_ms": elapsed,
                "code_lines": code.count("\n") + 1,
            }
        )

        status = "✅" if has_code else "❌"
        print_msg(f"      {status} Generated {code.count(chr(10)) + 1} lines in {elapsed:.0f}ms")

    passed = sum(1 for r in results if r["success"])
    print_msg(f"\n   Results: {passed}/{len(tests)} passed")

    return results


def generate_results_html(provider_info, gen_results):
    """Generate HTML report with charts."""

    # Calculate stats
    total = len(gen_results)
    passed = sum(1 for r in gen_results if r["success"])
    avg_time = sum(r["time_ms"] for r in gen_results) / total if total else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Agent Sandbox Benchmark Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 40px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ 
            font-size: 2.5rem; 
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #888; margin-bottom: 40px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
        }}
        .card h3 {{ color: #00d9ff; margin-bottom: 8px; font-size: 0.9rem; text-transform: uppercase; }}
        .card .value {{ font-size: 2.5rem; font-weight: 700; }}
        .card .unit {{ color: #888; font-size: 1rem; }}
        .chart-container {{ 
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .chart-title {{ margin-bottom: 20px; font-size: 1.2rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #00d9ff; font-weight: 600; }}
        .pass {{ color: #00ff88; }}
        .fail {{ color: #ff4757; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-success {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .badge-fail {{ background: rgba(255,71,87,0.2); color: #ff4757; }}
        .footer {{ text-align: center; margin-top: 40px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Agent Sandbox Runtime</h1>
        <p class="subtitle">Benchmark Results • {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        
        <div class="grid">
            <div class="card">
                <h3>Provider</h3>
                <div class="value">{provider_info["provider"].upper()}</div>
                <div class="unit">{provider_info["model"]}</div>
            </div>
            <div class="card">
                <h3>Success Rate</h3>
                <div class="value">{passed / total * 100:.0f}<span class="unit">%</span></div>
                <div class="unit">{passed}/{total} tests passed</div>
            </div>
            <div class="card">
                <h3>Avg Response Time</h3>
                <div class="value">{avg_time:.0f}<span class="unit">ms</span></div>
                <div class="unit">per generation</div>
            </div>
            <div class="card">
                <h3>API Latency</h3>
                <div class="value">{
        provider_info["latency_ms"]:.0f}<span class="unit">ms</span></div>
                <div class="unit">provider ping</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">📊 Response Times by Test</h3>
            <canvas id="timeChart" height="100"></canvas>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">📈 Success Rate</h3>
            <canvas id="successChart" height="80"></canvas>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">📋 Test Results</h3>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Status</th>
                    <th>Time</th>
                    <th>Lines</th>
                </tr>
                {
        "".join(
            f'''
                <tr>
                    <td>{r["task"][:50]}</td>
                    <td><span class="badge {"badge-success" if r["success"] else "badge-fail"}">{"PASS" if r["success"] else "FAIL"}</span></td>
                    <td>{r["time_ms"]:.0f}ms</td>
                    <td>{r["code_lines"]}</td>
                </tr>'''
            for r in gen_results
        )
    }
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Agent Sandbox Runtime v0.1.0</p>
        </div>
    </div>
    
    <script>
        // Time chart
        new Chart(document.getElementById('timeChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([f"Test {i + 1}" for i in range(len(gen_results))])},
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: {json.dumps([r["time_ms"] for r in gen_results])},
                    backgroundColor: 'rgba(0, 217, 255, 0.6)',
                    borderColor: 'rgba(0, 217, 255, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ 
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#888' }}
                    }},
                    x: {{ 
                        grid: {{ display: false }},
                        ticks: {{ color: '#888' }}
                    }}
                }}
            }}
        }});
        
        // Success chart
        new Chart(document.getElementById('successChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed'],
                datasets: [{{
                    data: [{passed}, {total - passed}],
                    backgroundColor: ['rgba(0, 255, 136, 0.8)', 'rgba(255, 71, 87, 0.8)'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ 
                        position: 'right',
                        labels: {{ color: '#fff' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return html


async def main():
    print_msg(
        Panel.fit(
            "[bold cyan]🚀 Agent Sandbox Runtime[/bold cyan]\n[dim]Full System Benchmark[/dim]",
            border_style="cyan",
        )
        if RICH
        else "=== Agent Sandbox Benchmark ==="
    )

    # Run tests
    provider_info = await test_provider()
    gen_results = await run_code_generation_tests()

    # Generate report
    html = generate_results_html(provider_info, gen_results)

    report_path = Path("benchmark_results.html")
    report_path.write_text(html)

    print_msg(f"\n📄 Report saved: {report_path.absolute()}", style="bold green")

    # Summary
    passed = sum(1 for r in gen_results if r["success"])
    total = len(gen_results)

    if RICH:
        table = Table(title="Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Provider", provider_info["provider"])
        table.add_row("Model", provider_info["model"])
        table.add_row("Tests Passed", f"{passed}/{total}")
        table.add_row("Success Rate", f"{passed / total * 100:.0f}%")
        table.add_row("Avg Time", f"{sum(r['time_ms'] for r in gen_results) / total:.0f}ms")
        console.print(table)

    print_msg("\n✨ Benchmark complete!", style="bold")


if __name__ == "__main__":
    asyncio.run(main())
