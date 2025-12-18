#!/usr/bin/env python3
"""
Demo Script
============

Quick demonstration of the agent's self-correcting capabilities.

Run: python scripts/demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main():
    """Run the demo."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax

    from agent_sandbox.runtime import AgentRuntime

    console = Console()

    console.print(
        Panel.fit(
            "[bold green]🚀 Agent Sandbox Runtime Demo[/bold green]\n\n"
            "Watch the agent write code, execute it safely,\n"
            "and self-correct any errors.",
            border_style="green",
        )
    )

    # Demo tasks
    tasks = [
        {
            "name": "Simple Math",
            "task": "Write a function to calculate the factorial of 10 and print the result.",
        },
        {
            "name": "Error Recovery",
            "task": "Write a function that calculates fibonacci(20) using recursion. Print the result.",
        },
        {
            "name": "Data Processing",
            "task": 'Parse this JSON and print the names: [{"name": "Alice"}, {"name": "Bob"}]',
        },
    ]

    async with AgentRuntime() as runtime:
        for demo in tasks:
            console.print(f"\n[bold cyan]═══ {demo['name']} ═══[/bold cyan]")
            console.print(f"[dim]Task: {demo['task']}[/dim]\n")

            result = await runtime.run(demo["task"])

            if result["success"]:
                console.print("[green]✓ Success![/green]")
            else:
                console.print("[red]✗ Failed[/red]")

            console.print(f"[dim]Attempts: {result['attempts']}[/dim]")

            if result["code"]:
                syntax = Syntax(result["code"], "python", theme="monokai", line_numbers=True)
                console.print(syntax)

            if result["output"]:
                console.print(
                    Panel(
                        result["output"],
                        title="Output",
                        border_style="green" if result["success"] else "red",
                    )
                )

            console.print()

    console.print("[bold green]✨ Demo complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
