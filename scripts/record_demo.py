#!/usr/bin/env python3
"""
DEMO RECORDER - Creates terminal animation for README/Twitter
=============================================================
This creates an animated demo showing the self-correcting agent in action.
Run: python scripts/record_demo.py
"""

import asyncio
import time
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table

console = Console(record=True)  # Enable recording


def slow_print(text, delay=0.02, style=None):
    """Simulate typing effect."""
    for char in text:
        console.print(char, end="", style=style)
        time.sleep(delay)
    console.print()


async def run_demo():
    """Run the demo that shows self-correction."""

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🚀 AGENT SANDBOX RUNTIME[/bold cyan]\n"
            "[dim]Self-Correcting AI Code Agent[/dim]",
            border_style="cyan",
        )
    )
    time.sleep(1)

    # Task
    console.print("\n[bold yellow]📝 Task:[/bold yellow]")
    slow_print('   "Fetch data from https://api.example.com/users"', delay=0.03, style="white")
    time.sleep(0.5)

    # Attempt 1
    console.print("\n[bold blue]⚡ Attempt 1: Generating code...[/bold blue]")
    time.sleep(0.8)

    console.print(
        Panel(
            """[cyan]import requests
response = requests.get("https://api.example.com/users")
print(response.json())[/cyan]""",
            title="Generated Code",
            border_style="blue",
        )
    )
    time.sleep(0.5)

    console.print("[dim]   Executing in Docker sandbox...[/dim]")
    time.sleep(1)

    # Error
    console.print("\n[bold red]❌ ERROR:[/bold red]")
    console.print("[red]   ModuleNotFoundError: No module named 'requests'[/red]")
    time.sleep(0.8)

    # Critic
    console.print("\n[bold yellow]🔍 Critic analyzing...[/bold yellow]")
    time.sleep(0.6)
    console.print(
        "[dim]   \"The 'requests' library is not installed. Use 'httpx' which is built-in.\"[/dim]"
    )
    time.sleep(0.8)

    # Attempt 2
    console.print("\n[bold blue]⚡ Attempt 2: Generating fixed code...[/bold blue]")
    time.sleep(0.8)

    console.print(
        Panel(
            """[green]import httpx
response = httpx.get("https://api.example.com/users")
print(response.json())[/green]""",
            title="Fixed Code",
            border_style="green",
        )
    )
    time.sleep(0.5)

    console.print("[dim]   Executing in Docker sandbox...[/dim]")
    time.sleep(1)

    # Success
    console.print("\n[bold green]✅ SUCCESS![/bold green]")
    console.print(
        '[green]   {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}[/green]'
    )
    time.sleep(0.5)

    # Summary
    console.print()
    table = Table(title="🎉 Completed", border_style="green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Attempts", "2")
    table.add_row("Self-Corrections", "1")
    table.add_row("Status", "✅ Success")
    console.print(table)

    console.print("\n[bold magenta]The agent fixed its own bug automatically![/bold magenta]")
    time.sleep(1)


async def main():
    await run_demo()

    # Save as HTML
    console.save_html("demo_recording.html")
    console.print("\n[dim]📄 Saved: demo_recording.html[/dim]")

    # Save as SVG (for README)
    console.save_svg("demo_recording.svg", title="Agent Sandbox Demo")
    console.print("[dim]📄 Saved: demo_recording.svg[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
